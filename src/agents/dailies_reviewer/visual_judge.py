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
        refs = _reference_images(shot)
        sheet = _reference_sheet(refs, Path(frame_paths[0]).parent) if refs else None
        note = (f"The LAST image is NOT part of the clip: it is a labelled board of the characters' reference images "
                f"({', '.join(r[0] for r in refs)}), canon for appearance only. Their plain studio background and pose "
                "are not expected in the clip. Every image before it is a frame of the generated clip.") if sheet else ""
        return self._review(frame_paths + ([str(sheet)] if sheet else []), kind, shot, prompt, global_style, note)

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
        review = self._agent.run(
            images=images,
            media_kind=media_kind,
            global_style=global_style or "(unspecified)",
            shot_context=_shot_context(shot),
            character_appearances=_appearances(shot),
            constraints=_constraints(shot),
            prompt=prompt,
            reference_note=reference_note,
        )
        return _gate(review)


# Accept/reject is decided from the checklist, not left to the VLM's own verdict: hard items must all hold; staging
# (positions, paths, sub-action order) only lowers the score. Free-form verdicts from a VLM over-weight blocking.
HARD_CHECKS = ("right_characters", "identity_matches", "main_action_shown", "integrity_ok", "constraints_ok")


def _gate(review: VisualReview) -> VisualReview:
    c = review.checks or {}
    if not all(k in c for k in HARD_CHECKS):
        return review
    ok = all(bool(c[k]) for k in HARD_CHECKS)
    if ok:
        review.accepted = True
        review.score = max(review.score, 0.9 if c.get("staging_matches", True) else 0.85)
        review.revised_prompt = None
    else:
        review.accepted = False
        review.score = min(review.score, 0.8)
    return review


def _reference_images(shot: ShotBlueprint, limit: int = 3):
    r = shot.render_layer
    cond = (r.image.conditioning if r and r.image else None)
    out = []
    for c in (cond.character_consistency if cond else []):
        for p in c.reference_image_paths[:1]:
            q = Path(p) if Path(p).is_absolute() else _HERE.parents[2] / p
            if q.exists():
                out.append((c.asset_id, str(q)))
    return out[:limit]


def _reference_sheet(refs, out_dir: Path) -> Path:
    """One board with every reference image side by side under a 'REFERENCE (not part of the clip)' banner, so the
    VLM cannot mistake a reference for a clip frame."""
    from PIL import Image, ImageDraw
    tiles = [Image.open(p).convert("RGB") for _, p in refs]
    h = 360; tiles = [t.resize((int(t.width * h / t.height), h)) for t in tiles]
    W = sum(t.width for t in tiles) + 20 * (len(tiles) + 1); board = Image.new("RGB", (W, h + 110), (30, 30, 30))
    d = ImageDraw.Draw(board)
    d.text((20, 15), "REFERENCE IMAGES - NOT PART OF THE CLIP", fill=(255, 220, 0))
    x = 20
    for (aid, _), t in zip(refs, tiles):
        board.paste(t, (x, 60)); d.text((x, h + 75), aid, fill=(255, 255, 255)); x += t.width + 20
    out = Path(out_dir) / "_reference_board.jpg"; board.save(out, quality=90)
    return out


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
        if n.continuity is not None:
            c = n.continuity
            lines.append(f"continuity: {c.time_of_day}, {c.weather}; lighting: {c.lighting or '-'}; props: "
                         + (", ".join(f"{p.prop_id}->{p.holder or p.location}" for p in c.props) or "-"))
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
