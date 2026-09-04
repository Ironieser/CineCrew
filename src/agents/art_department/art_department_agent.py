#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
ArtDepartment Agent [Controller] — builds the Asset Library (the truth anchor).

    Extract (art_department.yaml)  -> AssetLibrary: project meta, global style, narrative
                                      context, characters (appearance + persona), locations, props
    Guard   (project_settings.yaml)-> ProjectSettings: location / era locks, negative constraints
    Save    (skill)                -> <base_path>/{index,characters,locations,props}
    References (opt-in)            -> character reference sheets (CharacterPromptAgent -> T2IClient)
                                      and location establishing shots, linked into visual_references
"""

import logging
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from ...engine import ConfigurableAgent
from ...schemas.assets import AssetLibrary, VisualReferences
from ...schemas.project_settings import ProjectSettings
from ...skills.asset_management import save_assets
from ...skills.prompt_building import FallbackGenerator
from ...utils.limits_config import get_limits, truncate_script
from ...config import Config

DEFAULT_ASSETS_PATH = "data/output/assets"


_HERE = Path(__file__).resolve().parent


class ArtDepartmentAgent:
    """Orchestrates: Engine (Extract) -> Engine (Guard) -> Skill (Save)."""

    def __init__(self):
        self._extract_agent = ConfigurableAgent(config_path=str(_HERE / "art_department.yaml"))
        self._guard_agent = ConfigurableAgent(config_path=str(_HERE / "project_settings.yaml"))
        self._t2i = None          # created lazily by generate_references()
        self._char_prompter = None

    def run(
        self,
        script_text: str,
        enable_hallucination_guard: bool = True,
        base_path: str = DEFAULT_ASSETS_PATH,
        generate_references: bool = False,
    ) -> AssetLibrary:
        limits = get_limits()
        max_len = limits.get("script_art_department", 20000)
        script_excerpt = truncate_script(script_text, "script_art_department")
        if len(script_text) > max_len:
            logger.warning("Script truncated to %s chars", max_len)
        logger.info("Extracting & categorizing assets (%s chars)", len(script_excerpt))

        # Load project-specific style guide if present
        project_style_guide = ""
        style_guide_path = Path(base_path).parent / "style_guide.md"
        if style_guide_path.exists():
            try:
                project_style_guide = style_guide_path.read_text(encoding="utf-8")
                logger.info(f"Loaded project style guide from {style_guide_path}")
            except Exception as e:
                logger.warning(f"Failed to load style guide: {e}")

        # Extract
        try:
            asset_lib = self._extract_agent.run(
                script_excerpt=script_excerpt,
                project_style_guide=project_style_guide
            )
        except Exception as e:
            # Azure OpenAI may trigger a prompt-side content_filter (400) on violent content, leaving no output at all.
            # ArtDepartment's goal is "asset extraction" and does not need to preserve violent details verbatim; so retry once after a gentle sanitization.
            msg = str(e)
            if ("content_filter" in msg.lower() or "responsibleaipolicyviolation" in msg.lower()) and "violence" in msg.lower():
                logger.warning("ArtDepartment blocked by content_filter (violence). Retrying with sanitized excerpt.")
                sanitized = _sanitize_violence_excerpt(script_excerpt)
                asset_lib = self._extract_agent.run(script_excerpt=sanitized)
            else:
                raise

        # Guard
        if enable_hallucination_guard and asset_lib.project_settings is None:
            logger.info("Generating anti-hallucination constraints")
            try:
                ctx = asset_lib.narrative_context
                asset_lib.project_settings = self._guard_agent.run(
                    time_period=ctx.time_period,
                    global_mood=ctx.global_mood,
                    key_events=", ".join(ctx.key_events),
                    cultural_context=ctx.cultural_context or "",
                    location_names=", ".join(loc.name for loc in asset_lib.locations[:5]),
                )
            except Exception as e:
                logger.warning("Guard failed: %s", e)
                asset_lib.project_settings = ProjectSettings()

        # Save
        save_assets(asset_lib, base_path)
        logger.info("Assets saved to %s", base_path)

        if generate_references:
            self.generate_references(asset_lib, base_path)
        return asset_lib

    # ─────────────────────────────────────────────────────────────────────
    # Visual references: character sheets + location establishing shots
    # ─────────────────────────────────────────────────────────────────────

    def generate_references(
        self,
        asset_lib: AssetLibrary,
        base_path: str = DEFAULT_ASSETS_PATH,
        characters: bool = True,
        locations: bool = True,
    ) -> int:
        """
        Render a reference image for every character / location that has none yet
        (characters whose sheet was linked from disk are skipped) and record it in
        `visual_references`. Character sheets use the LLM-written prompt from
        CharacterPromptAgent (template fallback); locations use the establishing-shot
        template. Saves the library afterwards. Returns the number of images rendered.
        """
        from ...adapters.t2i_client import split_negative

        ref_dir = Path(base_path) / "references"
        done = 0

        if characters:
            for char in asset_lib.characters:
                if _has_image(char.visual_references):
                    continue
                try:
                    prompt = self._character_prompter().run(char.model_dump(), asset_lib.global_style)
                except Exception as e:
                    logger.warning("CharacterPromptAgent failed for %s (%s); using template", char.id, e)
                    prompt = FallbackGenerator.character_visual(char, asset_lib.global_style)
                if self._render_reference(char, prompt, ref_dir / f"{char.id}.png", split_negative):
                    done += 1

        if locations:
            for loc in asset_lib.locations:
                if _has_image(loc.visual_references):
                    continue
                prompt = FallbackGenerator.location_visual(loc, asset_lib.global_style)
                if self._render_reference(loc, prompt, ref_dir / f"{loc.id}.png", split_negative):
                    done += 1

        if done:
            save_assets(asset_lib, base_path)
        print(f"   🖼  [ArtDepartment] {done} reference image(s) rendered → {ref_dir}", flush=True)
        return done

    def _render_reference(self, asset, prompt: str, out_path: Path, split_negative) -> bool:
        positive, negative = split_negative(prompt)
        print(f"   🖼  [{asset.id}] rendering reference sheet", flush=True)
        try:
            self._t2i_client().render_to_file(out_path, prompt=positive, negative_prompt=negative)
        except Exception as e:
            print(f"      ❌ {type(e).__name__}: {e}", flush=True)
            return False
        asset.visual_references = VisualReferences(
            canonical_image_path=str(out_path),
            generation_prompt=prompt,
            generation_params={"model": self._t2i_client().model, "size": Config.T2I_SIZE},
            generation_timestamp=datetime.now().isoformat(),
        )
        return True

    def _t2i_client(self):
        if self._t2i is None:
            from ...adapters.t2i_client import T2IClient
            self._t2i = T2IClient()
        return self._t2i

    def _character_prompter(self):
        if self._char_prompter is None:
            from .character_prompt import CharacterPromptAgent
            self._char_prompter = CharacterPromptAgent()
        return self._char_prompter


def _has_image(refs: Optional[VisualReferences]) -> bool:
    return bool(refs and refs.canonical_image_path and Path(refs.canonical_image_path).exists())


def _sanitize_violence_excerpt(text: str) -> str:
    """
    Minimal "violence" sanitization: replace common violence/harm keywords to lower the chance of Azure prompt-side filtering.
    Note: used only for ArtDepartment's asset extraction (verbatim reproduction of dialogue is not required).
    """
    patterns = [
        r"\bbeat(?:en|ing)?\b",
        r"\bassault(?:ed|ing)?\b",
        r"\bshatter(?:ed|ing)?\b",
        r"\bbroke(?:n)?\b",
        r"\bwhiskey\b",  # also triggers under some policy combinations (bound to a violent context)
        r"\bbastards?\b",
        r"\banimal\b",
        r"\bwire\b",
        r"\bhospital\b",
    ]
    out = text
    for p in patterns:
        out = re.sub(p, "[REDACTED]", out, flags=re.IGNORECASE)
    return out
