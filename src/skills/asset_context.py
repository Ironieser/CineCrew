#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Asset Context Skill

Pure function: builds the formatted asset context string from AssetLibrary,
injected into the narrative / DSL prompt (used by the StoryEditor stage).
"""

from ..schemas.assets import AssetLibrary


def build_asset_context(asset_library: AssetLibrary) -> str:
    """
    Build the precise asset context string for injection into the StoryEditor prompt.

    Input: AssetLibrary (Pydantic model)
    Output: Formatted string (narrative context, global style, characters, locations, props)
    """
    context_parts = []

    # 0. Narrative context
    ctx = asset_library.narrative_context
    context_parts.append("### NARRATIVE CONTEXT (Read this first to understand the story world)")
    context_parts.append(f"Time Period: {ctx.time_period}")
    context_parts.append(f"Global Mood: {ctx.global_mood}")
    context_parts.append(f"Key Events: {', '.join(ctx.key_events)}")
    if ctx.cultural_context:
        context_parts.append(f"Cultural Context: {ctx.cultural_context}")
    context_parts.append("")

    # 1. Global style
    context_parts.append(f"### GLOBAL VISUAL STYLE\n{asset_library.global_style}\n")

    # 2. Characters
    context_parts.append("### CHARACTER ASSETS")
    for char in asset_library.characters:
        context_parts.append(f"- ID: {char.id}")
        context_parts.append(f"  Name: {char.name}")
        context_parts.append(f"  Visual: {char.description}")
        if char.clothing_style:
            context_parts.append(f"  Clothing: {char.clothing_style}")
        if char.personality:
            context_parts.append(f"  Personality: {char.personality}")
        if char.backstory:
            context_parts.append(f"  Backstory: {char.backstory}")
        if char.current_motivation:
            context_parts.append(f"  Motivation: {char.current_motivation}")
    context_parts.append("")

    # 3. Locations
    context_parts.append("### LOCATION ASSETS")
    for loc in asset_library.locations:
        context_parts.append(f"- ID: {loc.id}")
        context_parts.append(f"  Name: {loc.name} ({loc.type})")
        context_parts.append(f"  Visual: {loc.visual_style}")
        if loc.narrative_function:
            context_parts.append(f"  Narrative Function: {loc.narrative_function}")
    context_parts.append("")

    # 4. Props
    if asset_library.props:
        context_parts.append("### PROP ASSETS")
        for prop in asset_library.props:
            context_parts.append(f"- ID: {prop.id}")
            context_parts.append(f"  Name: {prop.name}")
            context_parts.append(f"  Description: {prop.visual_description}")
        context_parts.append("")

    return "\n".join(context_parts)
