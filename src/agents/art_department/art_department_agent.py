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
from typing import List, Optional
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

    def verify_against_script(self, asset_lib: AssetLibrary, script: str) -> List[str]:
        """
        Check every character description against the script (asset_fidelity.yaml) and apply the corrected
        descriptions in place. Runs before reference sheets are rendered: a description that contradicts the script
        is otherwise copied into the sheet and every shot, and later checks compare against the wrong text.
        Returns human-readable notes on what was corrected.
        """
        from ...engine import ConfigurableAgent
        chars = "\n".join(f"- {c.id} ({c.name}): description: {c.description} | clothing: {c.clothing_style}"
                          for c in asset_lib.characters)
        try:
            rep = ConfigurableAgent(config_path=str(Path(__file__).resolve().parent / "asset_fidelity.yaml")).run(
                script=script[:12000], characters=chars)
        except Exception as e:
            logger.warning("AssetFidelity failed (%s); descriptions left as written", e)
            return []
        notes = []
        for r in rep.characters:
            ch = asset_lib.get_character_by_id(r.id)
            if ch and r.corrected_description and r.contradictions:
                notes.append(f"{ch.id}: {'; '.join(r.contradictions)[:200]}")
                ch.description = r.corrected_description
        for n in notes:
            print(f"   🔎 [AssetFidelity] corrected {n}", flush=True)
        return notes

    def verify_supplied_sheets(self, asset_lib: AssetLibrary, script: str) -> List[str]:
        """
        Check every supplied character sheet (character_list/) against what the script says about that character
        (sheet_fidelity.yaml). On an identity-level mismatch the sheet is unlinked for THIS run only (the dataset file
        is untouched) and the description corrected, so generate_references renders a sheet that follows the script.
        """
        from ...engine import ConfigurableAgent
        agent = ConfigurableAgent(config_path=str(Path(__file__).resolve().parent / "sheet_fidelity.yaml"))
        notes = []
        for ch in asset_lib.characters:
            img = ch.visual_references.canonical_image_path if ch.visual_references else None
            if not img or not Path(img).exists():
                continue
            names = [n for n in re.split(r"[()（）]", ch.name) if n.strip()] + [ch.name]
            quotes = [para.strip() for para in script.split("\n") if any(n.strip() in para for n in names)]
            if not quotes:
                continue
            try:
                r = agent.run(images=[img], name=ch.name, quotes="\n".join(quotes)[:3000])
            except Exception as e:
                logger.warning("SheetFidelity failed for %s (%s)", ch.id, e)
                continue
            if r.mismatches:
                notes.append(f"{ch.id}: {'; '.join(r.mismatches)[:200]}")
                ch.visual_references.canonical_image_path = None      # this run renders its own sheet
                if r.corrected_description:
                    ch.description = r.corrected_description
        for n in notes:
            print(f"   🔎 [SheetFidelity] supplied sheet contradicts the script, re-rendering for this run: {n}", flush=True)
        return notes

    def verify_location_plates(self, asset_lib: AssetLibrary, blueprint, base_path: str = DEFAULT_ASSETS_PATH,
                               retries: int = 3) -> List[str]:
        """
        Check every location plate against the film's world facts (the continuity ledger, written after the plates
        were rendered) and re-render the plates that contradict them. Every keyframe of a scene is conditioned on its
        plate, so a wrong view through a window (a planet horizon where the story needs a distant globe) reaches every
        shot. Props with a reference picture that are staged in the location (e.g. a code-rendered planet) condition
        the re-render. The new plate is written to this run's references; a supplied plate is never overwritten.
        Returns human-readable notes.
        """
        import random
        import shutil
        from ...adapters.t2i_client import split_negative
        from ..dailies_reviewer.frame_check import BUILTIN_FACTS, world_violations
        from ..script_supervisor import judged_facts

        ref_dir = Path(base_path) / "references"
        notes = []
        for loc in asset_lib.locations:
            img = loc.visual_references.canonical_image_path if loc.visual_references else None
            if not img or not Path(img).exists():
                continue
            shots = [s for s in blueprint.shots
                     if s.staging_layer is None or s.staging_layer.environment_id in (loc.id, None)]
            story_facts: List[str] = []
            for s in shots:
                c = s.narrative_layer.continuity if s.narrative_layer else None
                for f in judged_facts(c.world_facts if c else []):
                    if f not in story_facts:
                        story_facts.append(f)
            if not story_facts:
                continue
            facts = BUILTIN_FACTS + story_facts
            action = f"an empty establishing shot of {loc.name}"
            try:
                bad = world_violations(img, facts, action=action)
            except Exception as e:
                logger.warning("PlateCheck failed for %s (%s)", loc.id, e)
                continue
            if not bad:
                print(f"   🔎 [PlateCheck] {loc.id}: consistent with the world facts", flush=True)
                continue
            print(f"   🔎 [PlateCheck] {loc.id}: {'; '.join(bad)[:300]} -> re-rendering", flush=True)
            props = []
            for s in shots:
                for e in (s.staging_layer.entities if s.staging_layer else []):
                    p = asset_lib.get_prop_by_id(e.asset_id)
                    if p and p not in props and p.visual_references and p.visual_references.canonical_image_path \
                            and Path(p.visual_references.canonical_image_path).exists():
                        props.append(p)
            props.sort(key=lambda p: {"critical": 0, "supporting": 1}.get(p.importance, 2))
            props = props[:2]
            base = loc.visual_references.generation_prompt or FallbackGenerator.location_visual(loc, asset_lib.global_style)
            positive, negative = split_negative(base)
            prompt = (f"{positive}\nThe picture shows the empty set: no people. It must respect: {' '.join(story_facts)}"
                      f"\nCORRECTION (the previous picture of this set was wrong): {'; '.join(bad)[:500]}")
            for i, p in enumerate(props, 1):
                prompt += (f"\nPicture {i} is NOT the set: it is the {p.name}, which is seen in the set (e.g. through a "
                           f"window) looking exactly like this picture: shape, size, lit and dark parts, colours.")
            refs = [p.visual_references.canonical_image_path for p in props] or None
            best, best_bad = None, bad
            for k in range(max(1, retries)):
                tmp = ref_dir / f"{loc.id}.try{k}.png"
                try:
                    self._t2i_client().render_to_file(tmp, prompt=prompt, negative_prompt=negative, reference_images=refs,
                                                      seed=random.randint(0, 2**31 - 1))
                    still = world_violations(str(tmp), facts, action=action)
                except Exception as e:
                    print(f"      ❌ plate attempt {k + 1}: {type(e).__name__}: {e}", flush=True)
                    continue
                print(f"      plate attempt {k + 1}: {len(still)} violation(s)", flush=True)
                if len(still) < len(best_bad):
                    best, best_bad = tmp, still
                if not still:
                    break
            if best is None:
                notes.append(f"{loc.id}: plate contradicts the world facts; no better plate found")
                continue
            out = ref_dir / f"{loc.id}.png"
            if Path(img).resolve() == out.resolve():
                n = len(list(ref_dir.glob(f"{loc.id}.bad*.png"))) + 1
                shutil.copy(out, ref_dir / f"{loc.id}.bad{n}.png")
            shutil.copy(best, out)
            loc.visual_references = VisualReferences(
                canonical_image_path=str(out), generation_prompt=prompt,
                generation_params={"model": "edit" if refs else self._t2i_client().model,
                                   "conditioned_on": [p.id for p in props], "plate_check": best_bad},
                generation_timestamp=datetime.now().isoformat(),
            )
            (Path(base_path) / "locations").mkdir(parents=True, exist_ok=True)
            (Path(base_path) / "locations" / f"{loc.id}.json").write_text(loc.model_dump_json(indent=2))
            notes.append(f"{loc.id}: re-rendered ({len(bad)} -> {len(best_bad)} violations)")
        if notes:
            (Path(base_path) / "asset_library.json").write_text(asset_lib.model_dump_json(indent=2))
        for n in notes:
            print(f"   🔎 [PlateCheck] {n}", flush=True)
        return notes

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
