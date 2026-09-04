#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
StoryEditorAgent — Blueprint Layer 1 populator
================================================

Responsibility (single):
  Read the script segment + AssetLibrary, identify shot boundaries,
  and fill the narrative_layer (narrative action, emotional beat, dialogue definition) for each shot.

Out of scope: shot scale, camera movement, lighting, entity positions, anything about "how to shoot it".
Those are handled by CinematographerAgent.
"""

from pathlib import Path

import sys
import uuid

from ...engine import ConfigurableAgent
from ...schemas.assets import AssetLibrary
from ...schemas.blueprint import SceneBlueprint, ShotBlueprint
from ...schemas.blueprint_partial import ShotNarrativeList
from ...skills import build_asset_context, build_hallucination_guard


_HERE = Path(__file__).resolve().parent


class StoryEditorAgent:
    """
    Script narrative analysis Agent.

    - Input: script_segment + AssetLibrary + an optional existing SceneBlueprint
    - Output: SceneBlueprint (shots include narrative_layer, staging_layer left as None)
    - Config: story_editor.yaml (co-located in this package)
    """

    def __init__(self):
        self._agent = ConfigurableAgent(config_path=str(_HERE / "story_editor.yaml"))

    def run(
        self,
        script_segment: str,
        asset_library: AssetLibrary,
        blueprint: SceneBlueprint | None = None,
    ) -> SceneBlueprint:
        """
        Analyze a script segment, generate the shot list, and populate the narrative_layer.

        If a blueprint is passed in, append shots (e.g. when calling on multi-act scripts in segments);
        otherwise initialize a blank Blueprint from the AssetLibrary.
        staging_layer / render_layer / assembly_layer are all left as None,
        to be filled by downstream Agents according to their responsibilities.
        """
        print("--- [StoryEditor] Analysing script → narrative_layer ---", flush=True)
        sys.stdout.flush()

        if blueprint is None:
            blueprint = SceneBlueprint.from_asset_library(
                asset_library,
                blueprint_id=f"blueprint_{uuid.uuid4().hex[:8]}",
            )

        asset_context = build_asset_context(asset_library)
        hallucination_guard = build_hallucination_guard(asset_library)

        result: ShotNarrativeList = self._agent.run(
            script_segment=script_segment,
            asset_context=asset_context,
            hallucination_guard=hallucination_guard,
        )

        for item in result.shots:
            blueprint.shots.append(
                ShotBlueprint(
                    shot_id=item.shot_id,
                    narrative_layer=item.narrative_layer,
                    # staging / render / assembly filled by downstream stages
                    staging_layer=None,
                    render_layer=None,
                    assembly_layer=None,
                )
            )

        print(
            f"   ✅ {len(result.shots)} shots added to Blueprint "
            f"(staging_layer pending)",
            flush=True,
        )
        return blueprint
