#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
CharacterPromptAgent — Asset Initial (part of the Art Department).

Turns a CharacterAsset (persona + appearance) into an optimized character
reference-sheet (T2I) prompt. See DEV_NOTES "Persona / character initialization".
"""

from pathlib import Path
from typing import Any, Dict, Optional

from ...engine import ConfigurableAgent
from ...skills.prompt_building import ContextBuilder

_HERE = Path(__file__).resolve().parent


class CharacterPromptAgent:
    """Optimize a character reference-sheet (T2I) prompt (character_prompt.yaml)."""

    def __init__(self, config_path: Optional[str] = None):
        self._agent = ConfigurableAgent(config_path=config_path or str(_HERE / "character_prompt.yaml"))

    def run(
        self,
        character: Dict[str, Any],
        global_style: str = "",
    ) -> str:
        """Return the optimized character reference-image prompt text."""
        character_context = ContextBuilder.character(character, global_style)
        result = self._agent.run(character_context=character_context)
        return result.prompt.strip()
