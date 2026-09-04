#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
VisualPromptTranslatorAgent — Step 2 of the Technical Director.

Translates storyboard visual prompts (t2i_prompt, i2v_prompt) and
character_appearances into cinematic English, then assembles the resolved
t2i / ti2i / i2v prompts by rule (replacing <asset_id> placeholders).
"""

from pathlib import Path
from typing import Dict, List, Optional

from ...engine import ConfigurableAgent
from ...schemas.prompts import TranslatedVisualPrompts

_HERE = Path(__file__).resolve().parent


def _inline(desc: str) -> str:
    """Appearance text as it is spliced into a sentence: no trailing period (avoids 'robe.'s eyes')."""
    return desc.strip().rstrip(".;,")


def _assemble_t2i_from_eng(
    t2i_prompt_eng: str,
    character_appearances: Dict[str, str],
) -> str:
    """Replace each <asset_id> in t2i_prompt_eng with character_appearances[asset_id]."""
    text = t2i_prompt_eng
    for asset_id, desc in (character_appearances or {}).items():
        text = text.replace(f"<{asset_id}>", _inline(desc))
    return text


def _assemble_ti2i_from_eng(
    t2i_prompt_eng: str,
    characters_in_shot: List[str],
    character_appearances: Dict[str, str],
) -> str:
    """Prefix with "Picture 1 is ...; Picture 2 is ..." and replace each <asset_id> with Picture 1/2/3."""
    order = characters_in_shot or []
    appearances = character_appearances or {}
    if not order:
        return _assemble_t2i_from_eng(t2i_prompt_eng, appearances)
    prefix = "; ".join(
        f"Picture {i + 1} is {_inline(appearances.get(cid, cid))}" for i, cid in enumerate(order)
    ) + ".\n"
    text = t2i_prompt_eng
    for i, cid in enumerate(order):
        text = text.replace(f"<{cid}>", f"Picture {i + 1}")
    return prefix + text


def _assemble_i2v_from_eng(
    i2v_prompt_eng: str,
    character_appearances: Dict[str, str],
) -> str:
    """Replace each <asset_id> in i2v_prompt_eng with character_appearances[asset_id]."""
    text = i2v_prompt_eng
    for asset_id, desc in (character_appearances or {}).items():
        text = text.replace(f"<{asset_id}>", _inline(desc))
    return text


class VisualPromptTranslatorAgent:
    """Translate + assemble t2i/ti2i/i2v prompts (visual_prompt_translator.yaml)."""

    def __init__(self):
        self._agent = ConfigurableAgent(config_path=str(_HERE / "visual_prompt_translator.yaml"))

    def run(
        self,
        current_dialogue: str,
        t2i_prompt: str,
        i2v_prompt: str,
        prev_segments: Optional[List[str]] = None,
        next_segments: Optional[List[str]] = None,
        prev_dialogue: Optional[str] = None,
        next_dialogue: Optional[str] = None,
        characters_in_shot: Optional[List[str]] = None,
        character_appearances: Optional[Dict[str, str]] = None,
    ) -> TranslatedVisualPrompts:
        """Translate t2i_prompt / i2v_prompt / character_appearances into English,
        then assemble t2i / ti2i / i2v by rule.
        current_dialogue: the full dialogue of the current segment.
        prev_segments: preceding dialogue lines (far -> near), ~2 by default;
            if omitted, prev_dialogue (single line) is used for compatibility.
        next_segments: following dialogue lines (near -> far), ~2 by default;
            if omitted, next_dialogue (single line) is used for compatibility."""
        prev_list = prev_segments if prev_segments is not None else ([prev_dialogue] if prev_dialogue else [])
        next_list = next_segments if next_segments is not None else ([next_dialogue] if next_dialogue else [])
        prev_segments_text = "\n".join(f"- Previous {i + 1}: {s}" for i, s in enumerate(prev_list)) if prev_list else "(none)"
        next_segments_text = "\n".join(f"- Next {i + 1}: {s}" for i, s in enumerate(next_list)) if next_list else "(none)"
        appearances = character_appearances or {}
        character_appearances_text = "\n".join(f"- {k}: {v}" for k, v in appearances.items()) if appearances else "(none)"
        result = self._agent.run(
            prev_segments_text=prev_segments_text,
            current_dialogue=current_dialogue or "",
            next_segments_text=next_segments_text,
            t2i_prompt=t2i_prompt or "",
            i2v_prompt=i2v_prompt or "",
            character_appearances_text=character_appearances_text,
        )
        # When assembling, prefer the LLM's English appearances; fall back to the originals for missing keys.
        eng_appearances = dict(result.character_appearances_eng) if result.character_appearances_eng else {}
        for k, v in appearances.items():
            if k not in eng_appearances:
                eng_appearances[k] = v
        chars = characters_in_shot or list(appearances.keys())
        t2i = _assemble_t2i_from_eng(result.t2i_prompt_eng, eng_appearances)
        ti2i = _assemble_ti2i_from_eng(result.t2i_prompt_eng, chars, eng_appearances)
        i2v = _assemble_i2v_from_eng(result.i2v_prompt_eng, eng_appearances)
        return TranslatedVisualPrompts(
            t2i_prompt_eng=result.t2i_prompt_eng,
            i2v_prompt_eng=result.i2v_prompt_eng,
            character_appearances_eng=eng_appearances,
            t2i=t2i,
            ti2i=ti2i,
            i2v=i2v,
        )
