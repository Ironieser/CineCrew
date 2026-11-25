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
import re
from pathlib import Path
from typing import List, Optional

from ...engine import ConfigurableAgent
from ...schemas.assets import AssetLibrary
from ...schemas.blueprint import ShotBlueprint
from ...schemas.critic import FrameCheck
from ..script_supervisor import judged_facts
from .visual_judge import _reference_images, _reference_sheet

_HERE = Path(__file__).resolve().parent
# built-in fact checked for every frame (generators duplicate planets / suns across a window and a sky)
BUILTIN_FACTS = ["Each one-of-a-kind celestial body (a particular planet, the sun, a moon) appears at most once."]
_DARK = {"night": {"night"}, "dusk": {"dusk", "night", "day"}, "dawn": {"dawn", "day", "dusk"}, "day": {"day", "dusk", "dawn"}}


_NONHUMAN = re.compile(r"\b(?:robot|android|droid|machine|dog|puppy|cat|kitten|bird|parrot|horse|animal|creature|shiba|"
                       r"retriever|terrier|tabby)\b|机器人|柴犬|小狗|小猫|狗|猫", re.I)


def human_cast(library: AssetLibrary) -> List[str]:
    """Names of the cast members who are people (robots and animals are not counted as humans)."""
    return [c.name for c in library.characters
            if not _NONHUMAN.search(f"{c.name} {c.description or ''} {c.clothing_style or ''}")]


def count_humans(image: str) -> List[str]:
    """Every human in `image` (count_humans.yaml): one entry each, background people included."""
    return ConfigurableAgent(config_path=str(_HERE / "count_humans.yaml")).run(images=[image]).humans


def closed_cast(facts) -> bool:
    """The ledger forbids anyone but the cast ("no people other than X and Y appear")."""
    from ..script_supervisor.script_supervisor_agent import _PRESENCE
    return any(_PRESENCE.search(f or "") for f in (facts or []))


_DISC = re.compile(r"\b(?:disc|disk|sphere|globe|ball|orb)\b", re.I)
_BODY = re.compile(r"\b(earth|moon|sun|mars|jupiter|saturn|venus|planet)\b", re.I)


def framing_checks(image: str, facts: List[str]) -> List[dict]:
    """Deterministic verdict on how a planet is framed. A fact that shows a body as a disc / sphere / globe is violated
    when the body's outline is cut off (body_framing.yaml: one focused question; inside a full description the VLM
    called an orbital horizon "whole"). Asked only when such a fact exists."""
    framing = [(i, f) for i, f in enumerate(facts, 1) if is_framing_fact(f)]
    if not framing:
        return []
    bodies = ConfigurableAgent(config_path=str(_HERE / "body_framing.yaml")).run(images=[image]).bodies
    out = []
    for i, f in framing:
        name = _BODY.search(f).group(1).lower()   # the body the fact is about (its first: "Earth ... from the Moon")
        cut = [b for b in bodies if (name in (b.name or "").lower() or (name == "planet" and b.name))
               and b.outline == "cut_off"]
        if cut:
            out.append({"fact": i, "verdict": "violated",
                        "evidence": f"the outline of {cut[0].name} is cut off (by the window frame or the picture edge, "
                                    f"or its surface fills the window like a horizon), not a whole {name} in space"})
    return out


def is_framing_fact(f: str) -> bool:
    """A fact about how a body is framed (shown as a disc / sphere): checked in code from the description's bodies."""
    return bool(_DISC.search(f or "") and _BODY.search(f or ""))


def judge_world(image: str, facts: List[str], cast: str = "none (no people)", action: str = "-") -> dict:
    """Blind description, then: framing facts in code (framing_checks), every other fact by the text-only judge.
    The text judge read a half-lit Earth as "the Moon" or "a partial disc" and failed framing facts it cannot judge
    reliably. Returns {"desc", "checks" (indexed on `facts`, 1-based), "action_shown", "action_reason"}."""
    desc = ConfigurableAgent(config_path=str(_HERE / "frame_describe.yaml")).run(images=[image])
    idx = [i for i, f in enumerate(facts, 1) if not is_framing_fact(f)]
    wv = ConfigurableAgent(config_path=str(_HERE / "world_judge.yaml")).run(
        action=action, cast=cast, facts=" ".join(f"({k}) {facts[i - 1]}" for k, i in enumerate(idx, 1)),
        description=desc.model_dump_json())
    checks = []
    for c in wv.checks:   # back onto the caller's numbering
        c = dict(c); k = int(c.get("fact") or 0)
        c["fact"] = idx[k - 1] if 1 <= k <= len(idx) else 0
        checks.append(c)
    return {"desc": desc, "checks": checks + framing_checks(image, facts),
            "action_shown": wv.action_shown, "action_reason": wv.action_reason}


def world_violations(image: str, facts: List[str], cast: str = "none (no people)", action: str = "-") -> List[str]:
    """judge_world for any still (a keyframe, a location plate). Returns "fact (seen: evidence)" per violated fact."""
    out = []
    for c in judge_world(image, facts, cast, action)["checks"]:
        if str(c.get("verdict", "")).lower() == "violated" and c.get("evidence"):
            i = int(c.get("fact") or 0)
            out.append(f"{facts[i - 1] if 1 <= i <= len(facts) else '?'} (seen: {c.get('evidence')})")
    return out


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
        fc = self._agent.run(
            images=[image] + ([str(board)] if board else []),
            reference_note=note,
            expected=", ".join(f"{names.get(c, c)}" for c in expected) or "none (no characters)",
            cast="; ".join(f"{c.name} ({(c.description or '')[:80]})" for c in library.characters),
            continuity=continuity_sentence(cont, library, set(expected)) if cont else "none",
            action=shot.narrative_layer.narrative_action,
        )
        if True:   # describe blind, then judge the facts from the text (no priming)
            facts = BUILTIN_FACTS + judged_facts(cont.world_facts if cont else [])
            jw = judge_world(image, facts, action=shot.narrative_layer.narrative_action,
                             cast="; ".join(f"{c.name}: {(c.description or '')[:100]}" for c in library.characters))
            desc = jw["desc"]
            fc.world_checks = jw["checks"] + [{"action_shown": jw["action_shown"], "action_reason": jw["action_reason"]}]
            fc.fix = (fc.fix + " " if fc.fix else "") + f"[seen: {desc.outside_view[:200]}]"
        if cont and closed_cast(cont.world_facts):   # closed cast: more humans than the cast has people = a stranger
            humans = count_humans(image)
            if len(humans) > len(human_cast(library)):
                fc.strangers = True
                fc.fix = (fc.fix + " " if fc.fix else "") + f"[{len(humans)} people seen: {'; '.join(humans)[:200]}]"
        return fc

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
        cont0 = shot.narrative_layer.continuity
        facts = BUILTIN_FACTS + judged_facts(cont0.world_facts if cont0 else [])
        viol = []
        for c in fc.world_checks:
            if "action_shown" in c:
                continue
            if str(c.get("verdict", "")).lower() == "violated" and c.get("evidence"):
                i = int(c.get("fact") or 0)
                viol.append(f"{facts[i - 1] if 1 <= i <= len(facts) else '?'} (seen: {c.get('evidence')})")
        if viol:
            out.append("contradicts the film's world: " + "; ".join(viol))
        if fc.bad_text:
            out.append("garbled text: " + "; ".join(fc.bad_text[:3]))
        act = next((c for c in fc.world_checks if "action_shown" in c), None)
        if act and str(act.get("action_shown", "")).lower() == "no":
            out.append("does not show the shot's main subject: " + str(act.get("action_reason", ""))[:160])
        cont = shot.narrative_layer.continuity
        if cont and cont.time_of_day != "none" and fc.time_of_day in _DARK and \
                fc.time_of_day not in _DARK.get(cont.time_of_day, {fc.time_of_day}):
            out.append(f"reads as {fc.time_of_day}, the shot is {cont.time_of_day}")
        return out
