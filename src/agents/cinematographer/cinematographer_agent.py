#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
CinematographerAgent — Blueprint Layer 2 populator
===============================================

Responsibility (single):
  Take a SceneBlueprint that already has a narrative_layer and decide how to shoot each shot:
  shot scale (shot_scale), angle, camera movement (movement), lighting,
  entity staging (entities + position/action_state), and hard visual constraints (consistency_constraints).

Does not interpret script content; does not modify narrative_layer; does not deal with T2I/T2V prompts.
"""

from pathlib import Path

import json
import sys

from ...engine import ConfigurableAgent
from ...schemas.assets import AssetLibrary
from ...schemas.blueprint import SceneBlueprint, StagingLayer
from ...schemas.blueprint_partial import ShotStagingList
from ...skills import build_asset_context, build_hallucination_guard


_HERE = Path(__file__).resolve().parent


class CinematographerAgent:
    """
    Shot staging Agent.

    - Input: SceneBlueprint (narrative_layer already populated) + AssetLibrary
    - Output: SceneBlueprint (staging_layer in place, other layers unchanged)
    - Config: cinematographer.yaml (co-located in this package)
    """

    def __init__(self):
        self._agent = ConfigurableAgent(config_path=str(_HERE / "cinematographer.yaml"))

    def run(
        self,
        blueprint: SceneBlueprint,
        asset_library: AssetLibrary,
    ) -> SceneBlueprint:
        """
        Iterate over blueprint.shots and fill staging information into each shot's staging_layer.

        Precondition: the narrative_layer of all shots has already been filled by StoryEditorAgent.
        Modifies the blueprint in place and returns it (for convenient chained calls).
        """
        shots_without_narrative = [
            s for s in blueprint.shots if s.narrative_layer is None
        ]
        if shots_without_narrative:
            raise RuntimeError(
                f"CinematographerAgent requires narrative_layer on all shots. "
                f"Missing on: {[s.shot_id for s in shots_without_narrative]}"
            )

        print(
            f"--- [Cinematographer] Staging {len(blueprint.shots)} shots → staging_layer ---",
            flush=True,
        )
        sys.stdout.flush()

        asset_context = build_asset_context(asset_library)
        hallucination_guard = build_hallucination_guard(asset_library)

        # Serialize the existing narrative_layer and pass it to the LLM
        shots_narrative_json = json.dumps(
            [
                {
                    "shot_id": s.shot_id,
                    "narrative_layer": s.narrative_layer.model_dump(),
                }
                for s in blueprint.shots
            ],
            ensure_ascii=False,
            indent=2,
        )

        result: ShotStagingList = self._agent.run(
            shots_narrative_json=shots_narrative_json,
            asset_context=asset_context,
            hallucination_guard=hallucination_guard,
        )

        # Write back aligned (match by shot_id to avoid ordering mismatches)
        staging_map = {item.shot_id: item.staging_layer for item in result.shots}
        matched = 0
        for shot in blueprint.shots:
            staging = staging_map.get(shot.shot_id)
            if staging is not None:
                shot.staging_layer = staging
                matched += 1
            else:
                print(
                    f"   ⚠️  [{shot.shot_id}] no staging_layer returned by LLM, "
                    f"using minimal fallback.",
                    flush=True,
                )
                shot.staging_layer = self._fallback_staging(shot.shot_id)

        print(
            f"   ✅ staging_layer filled: {matched}/{len(blueprint.shots)} shots matched",
            flush=True,
        )
        return blueprint

    @staticmethod
    def _fallback_staging(shot_id: str) -> StagingLayer:
        """Minimal valid fallback for when the LLM does not return staging for this shot."""
        from ...schemas.blueprint import CameraSpec
        return StagingLayer(
            duration_seconds=3.0,
            camera=CameraSpec(shot_scale="MS", angle="eye_level", movement="static"),
            lighting=None,
            environment_id=None,
            entities=[],
            consistency_constraints=[],
        )
