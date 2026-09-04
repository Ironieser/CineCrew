#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Centralized reading of `limits` in configs/pipeline_settings.yaml.

Architecture principle: "two truncation points"
- Gate A: script_art_department — max script length fed to the Art Department (global view).
- Gate B: script_segment_dsl — the script segment the pipeline hands to the DSL stages
  (StoryEditor, VODirector, ...); nothing downstream truncates the script again.
- The rest are field-length constraints, not script truncation.
"""
from pathlib import Path
from typing import Any, Dict

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SETTINGS_PATH = _PROJECT_ROOT / "configs" / "pipeline_settings.yaml"

# Kept in sync with pipeline_settings.yaml limits; used as defaults when a key is missing from the YAML
_DEFAULTS: Dict[str, int] = {
    # Physical input truncation (only these two)
    "script_art_department": 20000,
    "script_segment_dsl": 10000,
    # Field / content length
    "subject_action_max": 100,
    "director_note_excerpt": 500,
}

_cached: Dict[str, Any] | None = None


def get_limits(config_path: Path | None = None) -> Dict[str, int]:
    """Return the limits config (character counts). Keys match pipeline_settings.yaml limits; missing keys use _DEFAULTS."""
    global _cached
    path = config_path or _SETTINGS_PATH
    if _cached is not None and path == _SETTINGS_PATH:
        return _cached

    out = dict(_DEFAULTS)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            limits = data.get("limits") or {}
            for k, v in limits.items():
                if k in out and isinstance(v, (int, float)):
                    out[k] = int(v)
        except Exception:
            pass
    if path == _SETTINGS_PATH:
        _cached = out
    return out


def truncate_script(script: str, key: str, config_path: Path | None = None) -> str:
    """
    Truncate the script per limits[key]; return the original string if not over length.
    Used by the Art Department (Gate A); the DSL stages use the script_segment already cut by Gate B.
    """
    limits = get_limits(config_path)
    max_len = limits.get(key, _DEFAULTS.get(key, 10000))
    if len(script) <= max_len:
        return script
    return script[:max_len]
