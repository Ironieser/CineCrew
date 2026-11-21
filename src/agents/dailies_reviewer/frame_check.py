#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
FrameCheckAgent — calibrated, specific checks on a single keyframe (frame_check.yaml): identity vs the reference
sheets, missing characters, strangers, world facts, generated text, time of day. `failures()` turns a verdict into
the list of problems that block the keyframe; ProductionOperator iterates keyframes until it is empty.
"""
from pathlib import Path
from typing import List, Optional

from ...engine import ConfigurableAgent
from ...schemas.assets import AssetLibrary
from ...schemas.blueprint import ShotBlueprint
from ...schemas.critic import FrameCheck
from .visual_judge import _reference_images, _reference_sheet

_HERE = Path(__file__).resolve().parent
_DARK = {"night": {"night"}, "dusk": {"dusk", "night", "day"}, "dawn": {"dawn", "day", "dusk"}, "day": {"day", "dusk", "dawn"}}


class FrameCheckAgent:
    def __init__(self):
        self._agent = ConfigurableAgent(config_path=str(_HERE / "frame_check.yaml"))

    def check(self, image: str, shot: ShotBlueprint, library: AssetLibrary, expected: List[str]) -> FrameCheck:
        refs = [r for r in _reference_images(shot, limit=4) if r[0] in expected] or _reference_images(shot, limit=4)
        board = _reference_sheet(refs, Path(image).parent) if refs else None
        names = {c.id: c.name for c in library.characters}
        cont = shot.narrative_layer.continuity
        from ..script_supervisor import continuity_sentence
        note = (f"The LAST image is a labelled board of the expected characters' reference sheets "
                f"({', '.join(names.get(a, a) for a, _ in refs)}), canon for appearance; it is not the keyframe."
                if board else "No reference images are given.")
        return self._agent.run(
            images=[image] + ([str(board)] if board else []),
            reference_note=note,
            expected=", ".join(f"{names.get(c, c)}" for c in expected) or "none (no characters)",
            cast="; ".join(f"{c.name} ({(c.description or '')[:80]})" for c in library.characters),
            facts=" ".join(f"({i}) {f}" for i, f in enumerate(cont.world_facts, 1)) if cont and cont.world_facts else "none given",
            continuity=continuity_sentence(cont, library, set(expected)) if cont else "none",
            action=shot.narrative_layer.narrative_action,
        )

    @staticmethod
    def failures(fc: FrameCheck, shot: ShotBlueprint, expected_names: List[str]) -> List[str]:
        out = []
        if fc.identity_mismatch:
            out.append("does not match the reference: " + ", ".join(fc.identity_mismatch))
        missing = [m for m in fc.missing_characters if m in expected_names]
        if missing:
            out.append("missing: " + ", ".join(missing))
        if fc.strangers:
            out.append("a person outside the cast appears")
        if fc.world_violations:
            out.append("contradicts the film's world: " + "; ".join(fc.world_violations))
        if fc.bad_text:
            out.append("garbled text: " + "; ".join(fc.bad_text[:3]))
        cont = shot.narrative_layer.continuity
        if cont and cont.time_of_day != "none" and fc.time_of_day in _DARK and \
                fc.time_of_day not in _DARK.get(cont.time_of_day, {fc.time_of_day}):
            out.append(f"reads as {fc.time_of_day}, the shot is {cont.time_of_day}")
        return out
