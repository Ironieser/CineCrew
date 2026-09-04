#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Safety Guard Skill (Hallucination Guard)

Builds the critical-constraints prompt from AssetLibrary.project_settings
(the anti-hallucination guard injected during world building).
"""

from ..schemas.assets import AssetLibrary


def build_hallucination_guard(asset_library: AssetLibrary) -> str:
    """
    Build hallucination-guard prompt from ProjectSettings.

    If AssetLibrary has no project_settings, returns empty string.
    Otherwise returns a formatted block to inject into the system prompt.
    """
    if not asset_library.project_settings:
        return ""

    settings = asset_library.project_settings
    guard_prompt = "\n🛡️ **CRITICAL CONSTRAINTS (MUST FOLLOW)**:\n"
    constraint_items = []

    if settings.location_lock:
        guard_prompt += f"- **LOCATION LOCK**: {settings.location_lock}\n"
        constraint_items.append(f"LOCATION LOCK: {settings.location_lock}")

    if settings.era_lock:
        guard_prompt += f"- **ERA LOCK**: {settings.era_lock}\n"
        constraint_items.append(f"ERA LOCK: {settings.era_lock}")

    if settings.negative_constraints:
        guard_prompt += f"- **FORBIDDEN ELEMENTS**: {', '.join(settings.negative_constraints)}\n"
        constraint_items.append(f"FORBIDDEN: {', '.join(settings.negative_constraints)}")

    if settings.style_overrides:
        guard_prompt += "- **STYLE OVERRIDES**:\n"
        for key, value in settings.style_overrides.items():
            guard_prompt += f"  * {key}: {value}\n"
            constraint_items.append(f"{key.upper()}: {value}")

    guard_prompt += "\n⚠️ These constraints OVERRIDE any default associations in your training data.\n"
    guard_prompt += "For example: If 'Godfather' triggers 'Sicily', but LOCATION LOCK says 'New York', use New York.\n"

    if constraint_items:
        guard_prompt += "\n📋 **MANDATORY**: You MUST include ALL of the above constraints in the `consistency_constraints` field of EACH shot.\n"
        guard_prompt += "The `consistency_constraints` field MUST contain:\n"
        for item in constraint_items:
            guard_prompt += f"  - {item}\n"
        guard_prompt += "Plus any shot-specific visual consistency rules.\n"

    return guard_prompt
