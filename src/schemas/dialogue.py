# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""Dialogue extraction and emotion inference schemas (VODirectorAgent)."""
from pydantic import BaseModel, Field
from typing import List, Optional


class DialogueLine(BaseModel):
    """Single dialogue line (multi-speaker)."""
    speaker_id: str = Field(..., description="Speaker character ID")
    listener_id: str = Field(..., description="Listener character ID or 'audience'/'group'/'multiple'")
    text: str = Field(..., description="Dialogue text")
    order: int = Field(..., description="Order index (0-based)")


class DialogueExtraction(BaseModel):
    """LLM output: dialogue extracted for a shot."""
    shot_id: str = Field(..., description="Shot ID")
    full_dialogue: str = Field(..., description="Full dialogue text (all speakers combined)")
    speaker_id: str = Field(..., description="Main speaker ID or 'multiple'")
    listener_id: str = Field(..., description="Main listener ID or 'audience'/'group'/'none'")
    is_multi_speaker: bool = Field(default=False, description="Multiple speakers in shot")
    dialogue_lines: List[DialogueLine] = Field(default_factory=list, description="Per-line dialogue (multi-speaker)")
    sentences: List[str] = Field(default_factory=list, description="Sentences (backward compat)")


class EmotionInference(BaseModel):
    """LLM output: inferred emotion for a shot/segment."""
    emotion: str = Field(..., description="Emotion label (e.g. 'grief', 'anger', 'desperate')")
    intensity: int = Field(..., ge=1, le=10, description="Intensity 1-10")
    transition: Optional[str] = Field(None, description="Emotion transition description")
    reasoning: str = Field(..., description="Reasoning for debugging")
