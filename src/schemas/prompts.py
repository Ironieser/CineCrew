#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""LLM output schemas for the prompt-writing sub-agents."""
from typing import Dict

from pydantic import BaseModel, Field


class SinglePrompt(BaseModel):
    """Single optimized prompt text from an LLM (e.g. a character reference-sheet T2I prompt)."""
    prompt: str = Field(..., description="The optimized prompt text")


class VoiceDesignOutput(BaseModel):
    """VoiceDesign Agent output: a 4-section voice identity block for a TTS engine (stored on CharacterAsset.voice_design)."""
    voice_design: str = Field(..., description="Full 4-section block: Character Name, Voice Profile, Background, Personality")


class VisualPromptTranslatorOutput(BaseModel):
    """LLM output: translated t2i_prompt / i2v_prompt / character_appearances; t2i / ti2i / i2v are assembled by code following the rules."""
    t2i_prompt_eng: str = Field(..., description="Translated and refined T2I prompt (English), with <char_xxx> and Picture N preserved")
    i2v_prompt_eng: str = Field(..., description="Translated and refined I2V prompt (English), with <char_xxx> preserved")
    character_appearances_eng: Dict[str, str] = Field(
        default_factory=dict,
        description="Same keys as input character_appearances; values translated to cinematic English",
    )


class TranslatedVisualPrompts(BaseModel):
    """Complete output of the translator step: English templates + appearances + the rule-assembled t2i / ti2i / i2v."""
    t2i_prompt_eng: str = Field(..., description="Translated T2I template (English)")
    i2v_prompt_eng: str = Field(..., description="Translated I2V template (English)")
    character_appearances_eng: Dict[str, str] = Field(default_factory=dict, description="Character appearance descriptions in English")
    t2i: str = Field(..., description="t2i_prompt_eng with <char_id> replaced by character_appearances_eng")
    ti2i: str = Field(..., description="Picture N prefix + t2i_prompt_eng with <char_id> replaced by Picture 1, 2, 3")
    i2v: str = Field(..., description="i2v_prompt_eng with <char_id> replaced by character_appearances_eng")
