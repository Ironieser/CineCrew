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
        # coverage guard: every quoted line of the script must be spoken in some shot; one repair round with the
        # missing lines as feedback, keeping whichever shot list covers more
        from ...skills.script_coverage import missing_lines
        spoken = lambda r: [i.narrative_layer.dialogue.text or "" for i in r.shots]
        missing = missing_lines(script_segment, spoken(result))
        if missing:
            print(f"   ⚠️  [StoryEditor] {len(missing)} script line(s) not in any shot: {missing}; re-planning", flush=True)
            retry: ShotNarrativeList = self._agent.run(
                script_segment=script_segment,
                asset_context=asset_context,
                hallucination_guard=hallucination_guard,
                coverage_feedback=missing,
            )
            if len(missing_lines(script_segment, spoken(retry))) < len(missing):
                result = retry
            still = missing_lines(script_segment, spoken(result))
            if still:
                print(f"   ⚠️  [StoryEditor] still missing after re-plan: {still}", flush=True)
        # beat coverage: the key visual beats (a reveal, the closing image) must each be a shot
        try:
            beat_agent = ConfigurableAgent(config_path=str(_HERE / "beat_coverage.yaml"))
            listing = lambda r: "\n".join(f"- {i.shot_id}: {i.narrative_layer.narrative_action}" for i in r.shots)
            bc = beat_agent.run(script=script_segment, shots=listing(result))
            if bc.missing:
                print(f"   ⚠️  [StoryEditor] key beats with no shot: {bc.missing}; re-planning", flush=True)
                retry = self._agent.run(script_segment=script_segment, asset_context=asset_context,
                                        hallucination_guard=hallucination_guard,
                                        coverage_feedback=missing_lines(script_segment, spoken(result)),
                                        beat_feedback=bc.missing)
                bc2 = beat_agent.run(script=script_segment, shots=listing(retry))
                lines_ok = len(missing_lines(script_segment, spoken(retry))) <= len(missing_lines(script_segment, spoken(result)))
                if len(bc2.missing) < len(bc.missing) and lines_ok:
                    result = retry
                    print(f"   ✅ [StoryEditor] re-plan covers more beats (still missing: {bc2.missing})", flush=True)
        except Exception as e:
            print(f"   ⚠️  [StoryEditor] beat coverage check skipped ({e})", flush=True)

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
