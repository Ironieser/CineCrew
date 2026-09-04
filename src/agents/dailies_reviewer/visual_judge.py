#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
VisualJudgeAgent — VLM gate on generated media (part of the Dailies Reviewer).

DailiesReviewerAgent reviews the *prompts* before rendering. This agent reviews
the *result*: given a keyframe (one image) or a clip (a few sampled frames), it
scores fidelity to the shot spec and, on rejection, returns a revised prompt for
the next attempt. ProductionOperatorAgent.execute_jobs() runs the loop.
"""

from pathlib import Path
from typing import List

from ...engine import ConfigurableAgent
from ...schemas.blueprint import ShotBlueprint
from ...schemas.critic import VisualReview

_HERE = Path(__file__).resolve().parent


class VisualJudgeAgent:
    """Judge a generated keyframe / clip against its ShotBlueprint (visual_judge.yaml)."""

    def __init__(self):
        self._agent = ConfigurableAgent(config_path=str(_HERE / "visual_judge.yaml"))

    def review_keyframe(
        self,
        image_path: str,
        shot: ShotBlueprint,
        prompt: str,
        global_style: str = "",
        used_references: bool = False,
    ) -> VisualReview:
        note = (
            "The image was generated with the characters' reference sheets attached "
            "(Picture N refers to them); judge identity against those sheets."
            if used_references else ""
        )
        return self._review([image_path], "a generated keyframe (single image)", shot, prompt, global_style, note)

    def review_clip(
        self,
        frame_paths: List[str],
        shot: ShotBlueprint,
        prompt: str,
        global_style: str = "",
    ) -> VisualReview:
        kind = (
            "frames sampled from a generated video clip, in time order"
            if len(frame_paths) > 1
            else "a contact sheet of frames sampled from a generated video clip (read left-to-right, top-to-bottom)"
        )
        return self._review(frame_paths, kind, shot, prompt, global_style, "")

    # ------------------------------------------------------------------

    def _review(
        self,
        images: List[str],
        media_kind: str,
        shot: ShotBlueprint,
        prompt: str,
        global_style: str,
        reference_note: str,
    ) -> VisualReview:
        return self._agent.run(
            images=images,
            media_kind=media_kind,
            global_style=global_style or "(unspecified)",
            shot_context=_shot_context(shot),
            character_appearances=_appearances(shot),
            constraints=_constraints(shot),
            prompt=prompt,
            reference_note=reference_note,
        )


def _shot_context(shot: ShotBlueprint) -> str:
    n, s = shot.narrative_layer, shot.staging_layer
    lines = [f"shot_id: {shot.shot_id}"]
    if n:
        lines.append(f"action: {n.narrative_action}")
        lines.append(f"emotional beat: {n.emotional_beat}")
        if n.performance_emotion:
            lines.append(f"performance: {n.performance_emotion} ({n.performance_intensity or '-'}/10)")
        if n.dialogue.has_dialogue and n.dialogue.text:
            lines.append(f"dialogue ({n.dialogue.speaker_asset_id}): \"{n.dialogue.text}\"")
    if s:
        cam = s.camera
        lines.append(f"camera: scale={cam.shot_scale} angle={cam.angle} movement={cam.movement}")
        lines.append(f"lighting: {s.lighting}")
        lines.append(f"location: {s.environment_id}")
        if s.entities:
            lines.append("entities: " + "; ".join(
                f"{e.asset_id} ({e.position or '?'}, {e.action_state or 'idle'})" for e in s.entities
            ))
    return "\n".join(lines)


def _appearances(shot: ShotBlueprint) -> str:
    r = shot.render_layer
    if not r or not r.image.character_appearances:
        return "(none)"
    return "\n".join(f"- {k}: {v}" for k, v in r.image.character_appearances.items())


def _constraints(shot: ShotBlueprint) -> str:
    s = shot.staging_layer
    if not s or not s.consistency_constraints:
        return "(none)"
    return "\n".join(f"- {c}" for c in s.consistency_constraints)


__all__ = ["VisualJudgeAgent", "VisualReview"]
