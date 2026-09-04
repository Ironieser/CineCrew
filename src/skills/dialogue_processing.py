#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Dialogue / performance skills [The Hands] — context builders and rule fallbacks
for the VO Director. No LLM calls.
"""

from typing import Any, Dict, List, Optional

from ..schemas.assets import AssetLibrary
from ..schemas.blueprint import ShotBlueprint
from ..schemas.dialogue import EmotionInference


def build_character_context(library: AssetLibrary) -> str:
    """'Name → char_id' list for the dialogue extractor's ID mapping."""
    return "\n".join(f"  - {c.name} → {c.id}" for c in library.characters)


def fetch_speaker_metadata(speaker_id: Optional[str], library: AssetLibrary) -> Dict[str, str]:
    """Speaker persona fields consumed by emotion_inference.yaml (**kwargs)."""
    out = {"speaker_name": "Unknown", "speaker_personality": "N/A", "speaker_motivation": "N/A"}
    if not speaker_id or speaker_id in ("silent", "multiple", "group", "environment"):
        return out
    char = library.get_character_by_id(speaker_id)
    if char:
        out["speaker_name"] = char.name
        out["speaker_personality"] = char.personality or "N/A"
        out["speaker_motivation"] = char.current_motivation or "N/A"
    return out


def build_visual_context(shot: ShotBlueprint) -> str:
    """Staging + narrative of one shot as the visual context for extraction / emotion prompts."""
    parts = []
    s = shot.staging_layer
    if s is not None:
        parts += [
            f"Shot Scale: {s.camera.shot_scale or 'unspecified'}",
            f"Camera Angle: {s.camera.angle or 'eye_level'}",
            f"Camera Movement: {s.camera.movement or 'static'}",
            f"Lighting: {s.lighting or 'unspecified'}",
            f"Duration: {s.duration_seconds:.1f}s",
        ]
        if s.entities:
            parts.append("Entities: " + ", ".join(f"{e.asset_id}({e.action_state or 'idle'})" for e in s.entities))
    n = shot.narrative_layer
    if n is not None:
        parts.append(f"Narrative: {n.narrative_action}")
        parts.append(f"Emotion Beat: {n.emotional_beat}")
    return "\n".join(parts)


def format_emotion_history(history: List[Dict[str, Any]], last_n: int = 3) -> str:
    """Last `last_n` inferred emotions, for continuity."""
    tail = history[-last_n:] if history else []
    if not tail:
        return "  (No previous emotions)"
    return "\n".join(f"  - {h.get('shot_id', '?')}: {h.get('emotion', '?')}" for h in tail)


def get_fallback_emotion(text: str = "", camera_movement: Optional[str] = None) -> EmotionInference:
    """Rule-based emotion when the LLM call fails: dialogue keywords first, then camera energy."""
    t = (text or "").lower()
    if any(k in t for k in ("desperate", "please", "beg")):
        return EmotionInference(emotion="desperate", intensity=7, reasoning="Rule: keyword")
    if any(k in t for k in ("angry", "damn", "hell", "shut up")):
        return EmotionInference(emotion="anger", intensity=6, reasoning="Rule: keyword")
    mv = (camera_movement or "").lower()
    if any(k in mv for k in ("handheld", "whip", "fast", "rapid", "orbit")):
        return EmotionInference(emotion="chaotic", intensity=6, reasoning="Rule: high camera energy")
    if any(k in mv for k in ("static", "still", "locked")):
        return EmotionInference(emotion="peaceful", intensity=4, reasoning="Rule: static camera")
    return EmotionInference(emotion="neutral", intensity=5, reasoning="Rule: default")
