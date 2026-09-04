#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
VoiceDesignAgent — Asset Initial (part of the VO Director).

Designs a character's fixed voice and produces a TTS prompt (voice_design.yaml).
The prompt is used to synthesize the voice via TTS; the generated audio is then
linked to the character's audio_references.
"""

from pathlib import Path
from typing import Any, Dict

from ...engine import ConfigurableAgent
from ...skills.prompt_building import ContextBuilder

_HERE = Path(__file__).resolve().parent


class VoiceDesignAgent:
    """Design a character voice and emit a TTS prompt (voice_design.yaml).
    Returns VoiceDesignOutput; .voice_design is a 4-section Qwen3-TTS text block."""

    def __init__(self):
        self._agent = ConfigurableAgent(config_path=str(_HERE / "voice_design.yaml"))

    def run(
        self,
        character: Dict[str, Any],
        global_style: str = "",
    ):
        design_ctx = ContextBuilder.voice_design(character, global_style)
        return self._agent.run(**design_ctx)
