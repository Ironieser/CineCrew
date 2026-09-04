#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Dailies Reviewer schemas.

- ShotCriticResult : text-level critic over resolved prompts (5-shot sliding window),
                     produced by DailiesReviewerAgent before anything is rendered.
- VisualReview     : VLM verdict on a *generated* keyframe / clip, produced by
                     VisualJudgeAgent inside the execution loop (accept or retry).
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ShotCriticResult(BaseModel):
    """Critic verdict for a single shot (the middle of the 5-shot window)."""

    shot_id: str = Field(..., description="The shot being evaluated")

    needs_fix: bool = Field(
        default=False,
        description="True if the prompts have quality issues that warrant correction",
    )

    issues: Optional[str] = Field(
        default=None,
        description=(
            "Concise description of the problem(s) found. "
            "null when needs_fix=False."
        ),
    )

    fixed_resolved_t2i: Optional[str] = Field(
        default=None,
        description=(
            "Improved resolved_t2i prompt. "
            "Only provided when needs_fix=True. null otherwise."
        ),
    )

    fixed_resolved_ti2i: Optional[str] = Field(
        default=None,
        description=(
            "Improved resolved_ti2i prompt (with Picture N prefixes). "
            "Only provided when the original has resolved_ti2i and needs_fix=True."
        ),
    )

    fixed_resolved_i2v: Optional[str] = Field(
        default=None,
        description=(
            "Improved resolved_i2v prompt. "
            "Only provided when needs_fix=True. null otherwise."
        ),
    )


class VisualReview(BaseModel):
    """VLM judge verdict on generated media (one keyframe or one video clip)."""

    accepted: bool = Field(..., description="True if the media is usable as-is for this shot")
    score: float = Field(..., ge=0.0, le=1.0, description="Overall quality/fidelity score, 0-1")
    issues: List[str] = Field(
        default_factory=list,
        description="Concrete defects found (identity drift, wrong count of people, artifacts, wrong action, ...). Empty when accepted.",
    )
    revised_prompt: Optional[str] = Field(
        None,
        description=(
            "When not accepted: a complete rewritten generation prompt that addresses the issues "
            "(keep everything that was correct). null when accepted."
        ),
    )
    notes: str = Field("", description="One-sentence rationale")
