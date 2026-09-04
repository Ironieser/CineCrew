#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Memory / Knowledge Skill [The Memory]

Reads markdown from configs/knowledge/ for prompt injection.
YAML: {{ load_knowledge('rules/common/naming.md') }} or {{ load_knowledge('common/naming.md', 'rules') }}

Ablation control: set environment variable DISABLE_KNOWLEDGE=1 to suppress all
knowledge injection (used by ablation studies that test w/o workflow memory).
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_BASE_DIR = _PROJECT_ROOT / "configs" / "knowledge"


@lru_cache(maxsize=32)
def _load_knowledge_cached(path: str, subfolder: Optional[str] = None) -> str:
    """Internal cached loader — always reads from disk regardless of env vars."""
    if subfolder is not None:
        rel = f"{subfolder}/{path}"
    else:
        rel = path
    file_path = KNOWLEDGE_BASE_DIR / rel
    try:
        content = file_path.read_text(encoding="utf-8")
        return f"\n\n--- [KNOWLEDGE: {rel}] ---\n{content}\n-----------------------------\n"
    except FileNotFoundError:
        print(f"⚠️ Warning: Knowledge file not found: {file_path}")
        return ""


def load_knowledge(path: str, subfolder: Optional[str] = None) -> str:
    """
    Load markdown from configs/knowledge/.

    Path-style:  {{ load_knowledge('rules/common/naming.md') }}
    Legacy:      {{ load_knowledge('common/naming.md', 'rules') }}

    Returns empty string when DISABLE_KNOWLEDGE=1 is set in environment
    (used by ablation studies A1 / A2 / A4 that exclude workflow memory).
    """
    if os.environ.get("DISABLE_KNOWLEDGE") == "1":
        return ""
    return _load_knowledge_cached(path, subfolder)


@lru_cache(maxsize=16)
def load_module_specs(agent_name: str) -> str:
    """
    Load L2 module specifications for a given agent (e.g. ArtDepartmentAgent, StoryEditorAgent).
    Used in YAML as: {{ load_module_specs('ArtDepartmentAgent') }}
    """
    path = KNOWLEDGE_BASE_DIR / "rules" / "L2_MODULE_SPECS.md"
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    lines = content.split("\n")
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if start_idx is None and line.startswith("##") and agent_name in line:
            start_idx = i
            continue
        if start_idx is not None and line.startswith("##") and i > start_idx:
            if "Specifications" in line or any(x in line for x in ["🏗️", "🎬", "✂️", "🎤", "🎥"]):
                end_idx = i
                break
    if start_idx is None:
        return ""
    block = "\n".join(lines[start_idx : end_idx if end_idx is not None else len(lines)])
    return f"\n\n--- [L2: {agent_name}] ---\n{block}\n-----------------------------\n"
