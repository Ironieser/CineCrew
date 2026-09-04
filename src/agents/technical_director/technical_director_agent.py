#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
TechnicalDirectorAgent — Blueprint Layer 3 populator
==================================================

Responsibility (single): fill the render_layer for each ShotBlueprint.

Executed in two steps with strictly separated responsibilities:

  Step 1 — LLM template generation (technical_director.yaml)
    Input: narrative_layer + staging_layer (already filled)
    Output:
      - t2i_template       : first-frame keyframe description (static state before the action, with <asset_id>)
      - i2v_template       : motion description (the action in progress, with <asset_id>)
      - characters_in_shot : ordered list of visible character IDs for this shot
      - character_appearances: appearance description of each character in this shot

  Step 2 — Code assembly (VisualPromptTranslatorAgent)
    Input: Step 1 output + character appearances from the AssetLibrary
    Output:
      - resolved_t2i  : final T2I prompt (<asset_id> → appearance description)
      - resolved_ti2i : final Ti2I prompt ("Picture N is ..." prefix + substitution)
      - resolved_i2v  : final I2V prompt (<asset_id> → appearance description)

Dependencies:
  - technical_director.yaml (co-located in this package) (Step 1 LLM)
  - VisualPromptTranslatorAgent (Step 2 translation + assembly)
"""

from pathlib import Path

import json
import sys
from typing import Dict, List, Optional

from ...config import Config
from ...engine import ConfigurableAgent
from ...schemas.assets import AssetLibrary
from ...schemas.blueprint import (
    SceneBlueprint,
    ShotBlueprint,
    RenderLayer,
    ImageRenderSpec,
    VideoRenderSpec,
    VideoEngineParams,
    LipSyncConstraint,
    ConditioningSpec,
    CharacterConsistencyControl,
)
from ...schemas.render_template import ShotRenderTemplate, ShotRenderTemplateList
from .visual_prompt_translator import (
    VisualPromptTranslatorAgent,
    _assemble_t2i_from_eng,
    _assemble_ti2i_from_eng,
    _assemble_i2v_from_eng,
)
from ...skills import build_asset_context, build_hallucination_guard

# Maximum number of shots passed to the LLM per batch (to avoid an overly long context)
_BATCH_SIZE = 8


_HERE = Path(__file__).resolve().parent


class TechnicalDirectorAgent:
    """
    Uses technical_director.yaml (LLM) + VisualPromptTranslatorAgent (assembly)
    to fill each shot's render_layer with T2I/I2V templates and the final resolved prompts.
    """

    def __init__(self):
        self._template_agent = ConfigurableAgent(config_path=str(_HERE / "technical_director.yaml"))
        self._translator = VisualPromptTranslatorAgent()

    def run(
        self,
        blueprint: SceneBlueprint,
        asset_library: AssetLibrary,
    ) -> SceneBlueprint:
        """
        Iterate over blueprint.shots and populate each shot's render_layer.
        Modifies the blueprint in place and returns it (for convenient chained calls).
        """
        print(
            f"--- [TechnicalDirector] Processing {len(blueprint.shots)} shots "
            f"in batches of {_BATCH_SIZE} ---",
            flush=True,
        )
        sys.stdout.flush()

        asset_context = build_asset_context(asset_library)
        hallucination_guard = build_hallucination_guard(asset_library)
        global_style = blueprint.global_style or ""

        # Process in batches, collecting the LLM-generated templates keyed by shot_id
        template_map: Dict[str, ShotRenderTemplate] = {}
        shots = blueprint.shots
        for batch_start in range(0, len(shots), _BATCH_SIZE):
            batch = shots[batch_start : batch_start + _BATCH_SIZE]
            next_batch = shots[batch_start + _BATCH_SIZE : batch_start + _BATCH_SIZE + 2]
            batch_templates = self._generate_templates_batch(
                batch, next_batch, asset_context, hallucination_guard
            )
            for tmpl in batch_templates:
                template_map[tmpl.shot_id] = tmpl

        # Step 2: translate + assemble each shot (carrying dialogue context from adjacent shots)
        for idx, shot in enumerate(blueprint.shots):
            tmpl = template_map.get(shot.shot_id)
            if tmpl is None:
                print(
                    f"   ⚠️  [{shot.shot_id}] no template generated, using fallback.",
                    flush=True,
                )
                shot.render_layer = self._fallback_render_layer(shot, global_style)
                continue

            # Take the narrative text of the previous 2 / next 2 shots as translator context
            prev_contexts = [
                _shot_context_text(blueprint.shots[i])
                for i in range(max(0, idx - 2), idx)
            ]
            next_contexts = [
                _shot_context_text(blueprint.shots[i])
                for i in range(idx + 1, min(len(blueprint.shots), idx + 3))
            ]

            try:
                shot.render_layer = self._assemble_render_layer(
                    shot, tmpl, asset_library, global_style,
                    prev_contexts=prev_contexts,
                    next_contexts=next_contexts,
                )
                print(
                    f"   ✅ [{shot.shot_id}] render_layer filled "
                    f"(chars={tmpl.characters_in_shot})",
                    flush=True,
                )
            except Exception as e:
                print(
                    f"   ⚠️  [{shot.shot_id}] assembly failed: {e}. Using template-only fallback.",
                    flush=True,
                )
                shot.render_layer = self._template_only_render_layer(tmpl, shot)

        # Rendering the keyframes (+ VLM review) happens in ProductionOperatorAgent.execute_jobs().
        return blueprint

    # ─────────────────────────────────────────────────────────────────────
    # Step 1: LLM template generation
    # ─────────────────────────────────────────────────────────────────────

    def _generate_templates_batch(
        self,
        batch: List[ShotBlueprint],
        next_shots: List[ShotBlueprint],
        asset_context: str,
        hallucination_guard: str,
    ) -> List[ShotRenderTemplate]:
        """Call the technical_director.yaml LLM and return render templates for a batch of shots."""
        shots_json = json.dumps(
            [
                {
                    "shot_id": s.shot_id,
                    "narrative_layer": s.narrative_layer.model_dump(),
                    "staging_layer": s.staging_layer.model_dump() if s.staging_layer else {},
                }
                for s in batch
            ],
            ensure_ascii=False,
            indent=2,
        )

        next_shots_json = None
        if next_shots:
            next_shots_json = json.dumps(
                [
                    {
                        "shot_id": s.shot_id,
                        "narrative_layer": {"narrative_action": s.narrative_layer.narrative_action}
                        if s.narrative_layer
                        else {},
                    }
                    for s in next_shots
                ],
                ensure_ascii=False,
            )

        result: ShotRenderTemplateList = self._template_agent.run(
            shots_json=shots_json,
            next_shots_json=next_shots_json or "",
            asset_context=asset_context,
            hallucination_guard=hallucination_guard,
        )
        return result.shots

    # ─────────────────────────────────────────────────────────────────────
    # Step 2: translation + assembly
    # ─────────────────────────────────────────────────────────────────────

    def _assemble_render_layer(
        self,
        shot: ShotBlueprint,
        tmpl: ShotRenderTemplate,
        asset_library: AssetLibrary,
        global_style: str,
        prev_contexts: Optional[List[str]] = None,
        next_contexts: Optional[List[str]] = None,
    ) -> RenderLayer:
        """
        Call VisualPromptTranslatorAgent to translate the Chinese in the template into English,
        then assemble the final prompts with the existing _assemble_t2i / _assemble_ti2i / _assemble_i2v.

        prev_contexts / next_contexts: narrative/dialogue text from adjacent shots,
        passed to the translator to keep tone and emotion consistent across shots.
        """
        narrative = shot.narrative_layer
        staging = shot.staging_layer

        # The shot's primary text (dialogue first, otherwise the narrative action description)
        current_dialogue = narrative.dialogue.text or narrative.narrative_action

        translated = self._translator.run(
            current_dialogue=current_dialogue,
            t2i_prompt=tmpl.t2i_template,
            i2v_prompt=tmpl.i2v_template,
            prev_segments=prev_contexts or [],
            next_segments=next_contexts or [],
            characters_in_shot=tmpl.characters_in_shot,
            character_appearances=tmpl.character_appearances,
        )

        # Assemble the three prompt variants
        resolved_t2i = translated.t2i
        resolved_ti2i = translated.ti2i
        resolved_i2v = translated.i2v

        # Character consistency control (reference images)
        conditioning = self._build_conditioning(tmpl.characters_in_shot, asset_library)

        # Lip-sync constraint
        has_dialogue = narrative.dialogue.has_dialogue and bool(narrative.dialogue.text)
        lip_sync = LipSyncConstraint(
            enabled=has_dialogue,
            sync_method="musetalk" if has_dialogue else None,
            audio_source_ref="assembly_layer.audio_tracks[0]" if has_dialogue else None,
        )

        # Camera motion intensity
        movement = staging.camera.movement if staging and staging.camera else None
        motion_intensity = _estimate_motion_intensity(movement)

        return RenderLayer(
            image=ImageRenderSpec(
                engine=Config.T2I_MODEL,
                t2i_template=tmpl.t2i_template,
                characters_in_shot=tmpl.characters_in_shot,
                character_appearances=tmpl.character_appearances,
                resolved_t2i=resolved_t2i,
                resolved_ti2i=resolved_ti2i,
                negative_prompt=_build_negative_prompt(staging),
                conditioning=conditioning,
            ),
            video=VideoRenderSpec(
                engine=Config.VIDEO_MODEL,
                i2v_template=tmpl.i2v_template,
                resolved_i2v=resolved_i2v,
                engine_params=VideoEngineParams(
                    resolution=Config.VIDEO_SIZE,
                    fps=Config.VIDEO_FPS,
                    camera_motion_intensity=motion_intensity,
                ),
                lip_sync_constraint=lip_sync,
            ),
        )

    # ─────────────────────────────────────────────────────────────────────
    # Fallbacks
    # ─────────────────────────────────────────────────────────────────────

    def _template_only_render_layer(
        self, tmpl: ShotRenderTemplate, shot: ShotBlueprint
    ) -> RenderLayer:
        """When translation fails: keep the LLM template and fall back to simple substitution for the resolved fields."""
        appearances = tmpl.character_appearances
        resolved_t2i = _assemble_t2i_from_eng(tmpl.t2i_template, appearances)
        resolved_ti2i = _assemble_ti2i_from_eng(
            tmpl.t2i_template, tmpl.characters_in_shot, appearances
        )
        resolved_i2v = _assemble_i2v_from_eng(tmpl.i2v_template, appearances)
        return RenderLayer(
            image=ImageRenderSpec(
                t2i_template=tmpl.t2i_template,
                characters_in_shot=tmpl.characters_in_shot,
                character_appearances=appearances,
                resolved_t2i=resolved_t2i,
                resolved_ti2i=resolved_ti2i,
            ),
            video=VideoRenderSpec(
                i2v_template=tmpl.i2v_template,
                resolved_i2v=resolved_i2v,
            ),
        )

    def _fallback_render_layer(self, shot: ShotBlueprint, global_style: str) -> RenderLayer:
        """Minimal fallback when the LLM fails entirely."""
        narrative = shot.narrative_layer
        staging = shot.staging_layer
        entities = ", ".join(e.asset_id for e in (staging.entities if staging else []))
        t2i = (
            f"{global_style}. "
            f"{staging.lighting if staging else ''}. "
            f"Characters: {entities}. "
            f"{narrative.narrative_action}."
        ).strip()
        i2v = (
            f"Static camera. {narrative.narrative_action}. "
            f"Mouth remains tightly closed. No speaking. "
            f"Subtle ambient motion."
        )
        return RenderLayer(
            image=ImageRenderSpec(
                t2i_template=t2i,
                resolved_t2i=t2i,
                resolved_ti2i=t2i,
            ),
            video=VideoRenderSpec(
                i2v_template=i2v,
                resolved_i2v=i2v,
            ),
        )

    # ─────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────

    def _build_conditioning(
        self,
        characters_in_shot: List[str],
        asset_library: AssetLibrary,
    ) -> Optional[ConditioningSpec]:
        controls: List[CharacterConsistencyControl] = []
        for asset_id in characters_in_shot:
            char = asset_library.get_character_by_id(asset_id)
            if not char:
                continue
            ref_paths: List[str] = []
            if char.visual_references and char.visual_references.canonical_image_path:
                ref_paths.append(char.visual_references.canonical_image_path)
            if ref_paths:
                controls.append(
                    CharacterConsistencyControl(
                        asset_id=asset_id,
                        method="ip_adapter_faceid",
                        reference_image_paths=ref_paths,
                        weight=0.85,
                    )
                )
        return ConditioningSpec(character_consistency=controls) if controls else None


# ─────────────────────────────────────────────────────────────────────────
# Module-level helpers
# ─────────────────────────────────────────────────────────────────────────

def _shot_context_text(shot: ShotBlueprint) -> str:
    """
    Compress a ShotBlueprint into a single line of text for VisualPromptTranslatorAgent
    to use as prev_segments / next_segments context.

    Prefer dialogue; when there is none, use the narrative action description.
    """
    if shot.narrative_layer is None:
        return shot.shot_id
    dialogue = shot.narrative_layer.dialogue
    if dialogue.has_dialogue and dialogue.text:
        speaker = dialogue.speaker_asset_id or "?"
        return f"[{speaker}]: {dialogue.text}"
    return shot.narrative_layer.narrative_action


def _estimate_motion_intensity(movement: Optional[str]) -> float:
    if not movement:
        return 0.3
    mv = movement.lower()
    if "static" in mv or "still" in mv:
        return 0.1
    if "slow" in mv:
        return 0.3
    if any(k in mv for k in ["dolly", "pan", "tilt", "push"]):
        return 0.5
    if any(k in mv for k in ["fast", "rapid", "handheld", "orbit"]):
        return 0.8
    return 0.4


def _build_negative_prompt(staging) -> Optional[str]:
    if not staging:
        return None
    negatives = ["blurry", "low quality", "static image", "watermark"]
    for c in getattr(staging, "consistency_constraints", []):
        cl = c.lower()
        if "no daylight" in cl or "no bright" in cl:
            negatives.append("daylight, bright windows")
    return ", ".join(dict.fromkeys(negatives))
