#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
FilmDSL validation skill [The Hands] — deterministic checks of a SceneBlueprint
against its AssetLibrary (the truth anchor). No LLM.

Three functions, used in this order by DSLValidatorAgent:
  validate_blueprint()   -> list of issue dicts (critical = an ID that does not exist)
  auto_correct_ids()     -> remap near-miss IDs deterministically (case / underscore /
                            prefix differences, substring matches); returns applied fixes
  drop_unknown_ids()     -> last resort after LLM repair: remove what is still unknown
"""

import re
from typing import Any, Dict, List, Optional

from ..schemas.assets import AssetLibrary
from ..schemas.blueprint import SceneBlueprint

MIN_SHOT_SECONDS = 1.0      # DiT video models degrade below ~1s
MAX_SHOT_SECONDS = 60.0     # longer than this is almost always a hallucinated duration


def _issue(shot_id: str, issue_type: str, field: str, value: Any, severity: str, fix: str) -> Dict[str, Any]:
    return {
        "shot_id": shot_id,
        "issue_type": issue_type,
        "field_name": field,
        "current_value": str(value),
        "severity": severity,
        "suggested_fix": fix,
    }


def _ids(library: AssetLibrary):
    chars = {c.id for c in library.characters}
    locs = {l.id for l in library.locations}
    props = {p.id for p in library.props}
    return chars, locs, props


def validate_blueprint(blueprint: SceneBlueprint, library: AssetLibrary) -> List[Dict[str, Any]]:
    """Static checks. Critical issues are references to IDs that are not in the library."""
    chars, locs, props = _ids(library)
    entity_ids = chars | props
    issues: List[Dict[str, Any]] = []
    seen_shot_ids = set()

    for shot in blueprint.shots:
        sid = shot.shot_id
        if sid in seen_shot_ids:
            issues.append(_issue(sid, "duplicate_shot_id", "shot_id", sid, "critical", "Rename to a unique shot_id"))
        seen_shot_ids.add(sid)

        n = shot.narrative_layer
        if n is not None and n.dialogue.has_dialogue:
            spk = n.dialogue.speaker_asset_id
            if spk and spk not in chars:
                issues.append(_issue(sid, "unknown_speaker", "narrative_layer.dialogue.speaker_asset_id", spk,
                                     "critical", "Use a char_* ID from the AssetLibrary"))

        s = shot.staging_layer
        if s is None:
            issues.append(_issue(sid, "missing_staging", "staging_layer", None, "critical", "Cinematographer must fill staging_layer"))
            continue

        if s.environment_id and s.environment_id not in locs:
            issues.append(_issue(sid, "unknown_environment", "staging_layer.environment_id", s.environment_id,
                                 "critical", "Use a loc_* ID from the AssetLibrary"))

        seen_entities = set()
        for e in s.entities:
            if e.asset_id in locs:
                issues.append(_issue(sid, "location_as_entity", "staging_layer.entities", e.asset_id,
                                     "critical", "Locations belong in environment_id, not entities"))
            elif e.asset_id not in entity_ids:
                issues.append(_issue(sid, "unknown_entity", "staging_layer.entities", e.asset_id,
                                     "critical", "Use a char_* / prop_* ID from the AssetLibrary"))
            if e.asset_id in seen_entities:
                issues.append(_issue(sid, "duplicate_entity", "staging_layer.entities", e.asset_id,
                                     "warning", "List each entity once"))
            seen_entities.add(e.asset_id)

        if n is not None and n.dialogue.has_dialogue and n.dialogue.speaker_asset_id in chars \
                and s.entities and n.dialogue.speaker_asset_id not in seen_entities:
            issues.append(_issue(sid, "speaker_not_staged", "staging_layer.entities", n.dialogue.speaker_asset_id,
                                 "warning", "The speaker should normally be visible or explicitly off-screen"))

        if s.duration_seconds < MIN_SHOT_SECONDS:
            issues.append(_issue(sid, "duration_too_short", "staging_layer.duration_seconds", s.duration_seconds,
                                 "warning", f"Use at least {MIN_SHOT_SECONDS}s"))
        elif s.duration_seconds > MAX_SHOT_SECONDS:
            issues.append(_issue(sid, "duration_suspiciously_long", "staging_layer.duration_seconds", s.duration_seconds,
                                 "warning", "Split the shot or check the value"))
    return issues


# ── deterministic repair ──────────────────────────────────────────────────────

def _norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"^(char|loc|prop|loc_int|loc_ext)_", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def _best_match(bad: str, candidates) -> Optional[str]:
    """Exact-after-normalisation first, then unique substring containment."""
    nb = _norm(bad)
    if not nb:
        return None
    exact = [c for c in candidates if _norm(c) == nb]
    if len(exact) == 1:
        return exact[0]
    partial = [c for c in candidates if nb in _norm(c) or _norm(c) in nb]
    return partial[0] if len(partial) == 1 else None


def auto_correct_ids(blueprint: SceneBlueprint, library: AssetLibrary) -> List[Dict[str, Any]]:
    """Remap near-miss IDs in place. Returns the list of fixes applied."""
    chars, locs, props = _ids(library)
    fixes: List[Dict[str, Any]] = []

    for shot in blueprint.shots:
        n, s = shot.narrative_layer, shot.staging_layer
        if n is not None and n.dialogue.speaker_asset_id and n.dialogue.speaker_asset_id not in chars:
            m = _best_match(n.dialogue.speaker_asset_id, chars)
            if m:
                fixes.append({"shot_id": shot.shot_id, "field": "speaker_asset_id", "from": n.dialogue.speaker_asset_id, "to": m})
                n.dialogue.speaker_asset_id = m
        if s is None:
            continue
        if s.environment_id and s.environment_id not in locs:
            m = _best_match(s.environment_id, locs)
            if m:
                fixes.append({"shot_id": shot.shot_id, "field": "environment_id", "from": s.environment_id, "to": m})
                s.environment_id = m
        kept = []
        for e in s.entities:
            if e.asset_id in locs:
                # A location listed as an entity: move it to environment_id if that is empty.
                if not s.environment_id:
                    s.environment_id = e.asset_id
                fixes.append({"shot_id": shot.shot_id, "field": "entities", "from": e.asset_id, "to": "environment_id"})
                continue
            if e.asset_id not in chars | props:
                m = _best_match(e.asset_id, chars | props)
                if m:
                    fixes.append({"shot_id": shot.shot_id, "field": "entities", "from": e.asset_id, "to": m})
                    e.asset_id = m
            kept.append(e)
        s.entities = kept
    return fixes


def drop_unknown_ids(blueprint: SceneBlueprint, library: AssetLibrary) -> List[Dict[str, Any]]:
    """Remove whatever is still unknown so downstream stages never see a dangling ID."""
    chars, locs, props = _ids(library)
    dropped: List[Dict[str, Any]] = []
    for shot in blueprint.shots:
        n, s = shot.narrative_layer, shot.staging_layer
        if n is not None and n.dialogue.speaker_asset_id and n.dialogue.speaker_asset_id not in chars:
            dropped.append({"shot_id": shot.shot_id, "field": "speaker_asset_id", "value": n.dialogue.speaker_asset_id})
            n.dialogue.speaker_asset_id = None
        if s is None:
            continue
        if s.environment_id and s.environment_id not in locs:
            dropped.append({"shot_id": shot.shot_id, "field": "environment_id", "value": s.environment_id})
            s.environment_id = None
        before = len(s.entities)
        s.entities = [e for e in s.entities if e.asset_id in chars | props]
        for _ in range(before - len(s.entities)):
            dropped.append({"shot_id": shot.shot_id, "field": "entities", "value": "unknown entity removed"})
    return dropped
