#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
ScriptSupervisorAgent — the continuity ledger (shots[].narrative_layer.continuity).

One LLM call (script_supervisor.yaml) writes each shot's world state: time of day, weather, lighting, prop holders,
wardrobe. A deterministic pass then repairs it: unknown IDs are dropped, missing entries inherit the previous shot,
time of day never runs backwards, and a prop keeps its holder unless that shot records a change. Shot generators
lose exactly this kind of state between independently rendered shots; the ledger is written into each shot's prompt
(ProductionOperator) and checked on the rendered clip (VisualJudge, tools/qa_report.py).
"""

import logging
import re
from pathlib import Path
from typing import List

from ...engine import ConfigurableAgent
from ...schemas.assets import AssetLibrary
from ...schemas.blueprint import ContinuityState, PropState, SceneBlueprint

logger = logging.getLogger(__name__)
_HERE = Path(__file__).resolve().parent
_ORDER = {"dawn": 0, "day": 1, "dusk": 2, "night": 3, "none": 3}


class ScriptSupervisorAgent:
    def __init__(self):
        self._agent = ConfigurableAgent(config_path=str(_HERE / "script_supervisor.yaml"))

    def run(self, blueprint: SceneBlueprint, script: str, library: AssetLibrary) -> SceneBlueprint:
        chars = "\n".join(f"- {c.id}: {c.name}" for c in library.characters) or "(none)"
        props = "\n".join(f"- {p.id}: {p.name} — {p.visual_description}" for p in library.props) or "(none)"
        shots = "\n".join(
            f"- {s.shot_id}: {s.narrative_layer.narrative_action}"
            + (f" | on screen: {', '.join(e.asset_id for e in s.staging_layer.entities)}" if s.staging_layer else "")
            + (f" | says: \"{s.narrative_layer.dialogue.text}\"" if s.narrative_layer.dialogue.has_dialogue else "")
            for s in blueprint.shots
        )
        try:
            plan = self._agent.run(script=script, characters=chars, props=props, shots=shots)
            by_id = {x.shot_id: x.continuity for x in plan.shots}
            facts = [clean_fact(f) for f in plan.world_facts]
            for c in by_id.values():      # story-wide facts travel with every shot's entry
                c.world_facts = [f for f in facts if f]
        except Exception as e:
            logger.warning("ScriptSupervisor LLM call failed (%s); ledger left empty", e)
            return blueprint
        report = self.repair(blueprint, by_id, library)
        for line in report:
            print(f"   📋 {line}", flush=True)
        return blueprint

    @staticmethod
    def repair(blueprint: SceneBlueprint, by_id: dict, library: AssetLibrary) -> List[str]:
        """Deterministic pass over the LLM ledger; returns human-readable notes on what was fixed or changes."""
        char_ids = {c.id for c in library.characters}
        prop_ids = {p.id for p in library.props}
        notes, prev = [], None
        for shot in blueprint.shots:
            cur = by_id.get(shot.shot_id)
            if cur is None:
                cur = prev.model_copy(deep=True) if prev else ContinuityState()
                cur.changes = []
                notes.append(f"{shot.shot_id}: no ledger entry, inherited the previous shot")
            cur.props = [p for p in cur.props if p.prop_id in prop_ids]
            for p in cur.props:
                if p.holder and p.holder not in char_ids:
                    p.holder = None
            cur.wardrobe = {k: v for k, v in cur.wardrobe.items() if k in char_ids}
            if prev is not None:
                if "none" not in (cur.time_of_day, prev.time_of_day) and _ORDER[cur.time_of_day] < _ORDER[prev.time_of_day]:
                    notes.append(f"{shot.shot_id}: time_of_day {cur.time_of_day} < {prev.time_of_day}; kept {prev.time_of_day}")
                    cur.time_of_day = prev.time_of_day
                elif cur.time_of_day != prev.time_of_day:
                    notes.append(f"{shot.shot_id}: time of day {prev.time_of_day} -> {cur.time_of_day}")
                # `props` is the state at the start of the shot, `changes` what happens during it: a prop keeps its
                # holder unless the previous shot (or this one) records the hand-over
                changed = " ".join(cur.changes + prev.changes)
                have = {p.prop_id for p in cur.props}
                for pp in prev.props:
                    if pp.prop_id not in have:
                        cur.props.append(pp.model_copy())
                        continue
                    c = next(p for p in cur.props if p.prop_id == pp.prop_id)
                    if c.holder != pp.holder and pp.prop_id not in changed:
                        notes.append(f"{shot.shot_id}: {pp.prop_id} holder {pp.holder} -> {c.holder} without a recorded "
                                     f"change; kept {pp.holder}")
                        c.holder, c.location = pp.holder, pp.location
            shot.narrative_layer.continuity = cur
            prev = cur
        return notes


_EXPLAIN = re.compile(r",?\s*(?:indicating|suggesting|which (?:means|shows|indicates)|meaning|implying|as if|showing that)\b[^.;]*",
                      re.I)


def clean_fact(f: str) -> str:
    """World facts must be checkable from frames: drop explanatory clauses ("..., indicating abandonment") and turn
    'motionless' (a checker reads a spinning planet as moving) into 'stays at the same place in the sky'."""
    f = _EXPLAIN.sub("", f or "").strip().rstrip(",;")
    f = re.sub(r"\bmotionless\b", "staying at the same place (it may still spin)", f, flags=re.I)
    return f if f.endswith(".") else (f + "." if f else f)


_PRESENCE = re.compile(r"\b(?:people|persons?|characters?|anyone|anybody|nobody|no-?one|no one|one else|"
                       r"crew members?|(?:is|are) (?:present|alone))\b", re.I)


def judged_facts(facts) -> List[str]:
    """The world facts a frame is judged against. Who may be present is left to the stranger / presence detector
    (calibrated on labelled shots): a text judge reads "only X and Y are present" as "X and Y must both be visible"
    and fails frames that show only one of them. Presence facts still go into the generation prompt."""
    return [f for f in (facts or []) if f and not _PRESENCE.search(f)]


def continuity_sentence(c: ContinuityState, library: AssetLibrary, on_screen=None) -> str:
    """Prompt text for one shot's ledger entry (used by ProductionOperator). Props are mentioned only when held by
    someone on screen or changing in this shot, so fixed set dressing does not crowd the prompt."""
    if c is None:
        return ""
    names = {x.id: x.name for x in library.characters}
    pnames = {x.id: x.name for x in library.props}
    bits = ([f"It is {c.time_of_day}" + (f", {c.weather}" if c.weather and c.weather != "none" else "") + "."]
            if c.time_of_day != "none" else [])
    if c.lighting:
        bits.append(f"Lighting: {c.lighting}.")
    moving = " ".join(c.changes)
    for p in c.props:
        what = pnames.get(p.prop_id, p.prop_id)
        relevant = p.prop_id in moving or (p.holder and (on_screen is None or p.holder in on_screen))
        if not relevant:
            continue
        if p.holder:
            bits.append(f"The {what} is with {names.get(p.holder, p.holder)}" + (f" ({p.state})" if p.state else "") + ".")
        elif p.location:
            bits.append(f"The {what} is {p.location}.")
    for cid, w in c.wardrobe.items():
        if on_screen is not None and cid not in on_screen:
            continue
        bits.append(f"{names.get(cid, cid)}: {w}.")
    if c.world_facts:
        bits.append("Facts that always hold in this film: " + "; ".join(c.world_facts) + ".")
    for ch in c.changes:
        for i, n in {**names, **pnames}.items():
            ch = ch.replace(i, n)
        bits.append(f"In this shot: {ch}.")
    return "Continuity: " + " ".join(bits)
