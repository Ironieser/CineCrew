#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Prompt Building Skill [The Hands]

- ContextBuilder   : assembles the request text fed to a prompt-writing sub-agent
                     (character reference sheet, voice design).
- FallbackGenerator: pure-template asset-reference prompts used when no LLM is available.
Templates come from configs/prompts/skill_templates.yaml.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from jinja2 import Template

from ..schemas.assets import CharacterAsset, LocationAsset, PropAsset

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SKILL_TEMPLATES_PATH = _PROJECT_ROOT / "configs" / "prompts" / "skill_templates.yaml"
_cached_templates: Optional[Dict[str, str]] = None


def _get_skill_templates() -> Dict[str, str]:
    """Load configs/prompts/skill_templates.yaml once."""
    global _cached_templates
    if _cached_templates is None:
        out: Dict[str, str] = {}
        if _SKILL_TEMPLATES_PATH.exists():
            data = yaml.safe_load(_SKILL_TEMPLATES_PATH.read_text(encoding="utf-8")) or {}
            out = {k: v for k, v in data.items() if isinstance(v, str)}
        _cached_templates = out
    return _cached_templates


def _render(key: str, ctx: Dict[str, Any], fallback: str = "") -> str:
    """Render the YAML template `key` with ctx; use `fallback` when the key is missing."""
    tpl = _get_skill_templates().get(key) or fallback
    return Template(tpl).render(**ctx).strip()


class ContextBuilder:
    """Request blocks for the prompt-writing sub-agents."""

    @staticmethod
    def character(character: Dict[str, Any], global_style: str) -> str:
        """character_context for CharacterPromptAgent (character_prompt.yaml)."""
        ctx = {
            "id": character.get("id", "N/A"),
            "name": character.get("name", "N/A"),
            "description": character.get("description", "N/A"),
            "clothing_style": character.get("clothing_style") or "Not specified",
            "personality": character.get("personality") or "Not specified",
            "backstory": character.get("backstory") or "Not specified",
            "global_style": global_style,
        }
        return _render(
            "character_request", ctx,
            "**Character**: {{ name }} ({{ id }})\n**Physical Description**: {{ description }}\n**Global Style**: {{ global_style }}",
        )

    @staticmethod
    def voice_design(character: Dict[str, Any], global_style: str = "") -> Dict[str, Any]:
        """kwargs for VoiceDesignAgent (voice_design.yaml)."""
        return {
            "name": character.get("name", "N/A"),
            "description": character.get("description") or "Not specified",
            "personality": character.get("personality") or "Not specified",
            "backstory": character.get("backstory") or "Not specified",
            "voice_description": character.get("voice_description") or "None",
        }


_DEFAULT_CHARACTER_VISUAL = (
    "Professional character portrait photograph, {{ name }}, {{ description }},"
    "{% if has_clothing %} wearing {{ clothing_style }},{% endif %}"
    " neutral expression, facing camera directly, medium shot (head and shoulders),"
    " studio lighting, soft diffused light, plain neutral background,"
    " photorealistic, highly detailed, film photography aesthetic"
)
_DEFAULT_LOCATION_VISUAL = (
    "Establishing shot photograph, {{ name }}, {{ visual_style }}, wide angle, architectural photography,"
    " sharp focus, cinematic lighting, photorealistic, no people, empty scene"
    "{% if has_style %}, Style: {{ global_style }}{% endif %}\n\n"
    "Negative: people, characters, blurry, low quality, distorted perspective, anime, cartoon"
)
_DEFAULT_PROP_VISUAL = (
    "Product photography style, {{ visual_description }}, isolated on white background,"
    " studio lighting, soft shadows, highly detailed, photorealistic\n\n"
    "Negative: people, blurry, low quality, multiple objects, cluttered"
)


class FallbackGenerator:
    """Template-only asset reference prompts (used when the LLM prompt writer is unavailable)."""

    @staticmethod
    def character_visual(character: CharacterAsset, global_style: str = "") -> str:
        ctx = {
            "name": character.name,
            "description": character.description,
            "clothing_style": character.clothing_style or "",
            "has_clothing": bool(character.clothing_style),
        }
        return _render("character_visual", ctx, _DEFAULT_CHARACTER_VISUAL)

    @staticmethod
    def location_visual(location: LocationAsset, global_style: str = "") -> str:
        ctx = {
            "name": location.name,
            "visual_style": location.visual_style,
            "global_style": global_style or "",
            "has_style": bool(global_style),
        }
        return _render("location_visual", ctx, _DEFAULT_LOCATION_VISUAL)

    @staticmethod
    def prop_visual(prop: PropAsset) -> str:
        return _render("prop_visual", {"visual_description": prop.visual_description}, _DEFAULT_PROP_VISUAL)
