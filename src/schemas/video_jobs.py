#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
VideoJob / VideoJobBatch — the backend-agnostic video job spec.

The Production Operator turns each FilmDSL shot into one or more VideoJobs. A job is
just "prompt + optional keyframe + timing + size"; nothing here is tied to a specific
T2V model. `src/adapters/video_client.py` maps a job onto the OpenAI-style
`/videos` API so any compatible server (Sora, a self-hosted Wan / LTX wrapper, ...)
can execute it.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

DEFAULT_NEGATIVE_PROMPT = (
    "blurry faces, distorted anatomy, deformed hands, extra limbs, low resolution, artifacts"
)


class VideoJob(BaseModel):
    """One T2V / I2V generation request for a shot (or a segment of a shot)."""

    job_id: Optional[str] = Field(None, description="Unique job id (scene_shot_segment)")
    scene_id: str = Field(..., description="Scene / blueprint ID")
    shot_id: str = Field(..., description="Shot ID")
    segment_id: Optional[str] = Field(None, description="Segment ID if the shot was split")

    prompt: str = Field(..., description="Resolved video prompt (no <asset_id> placeholders)")
    negative_prompt: str = Field(default=DEFAULT_NEGATIVE_PROMPT)
    image_reference: Optional[str] = Field(
        None, description="Keyframe / reference image path; when set the job is I2V"
    )

    # Spoken line of this segment (dialogue_core only), forwarded to the video backend so a
    # joint audio-video model can voice it; a TTS stage can consume the same fields.
    dialogue: Optional[str] = Field(None, description="Verbatim line spoken in this segment")
    voice: Optional[str] = Field(None, description="TTS voice / preset id of the speaker")
    voice_instructions: Optional[str] = Field(None, description="Voice identity + performed emotion for the TTS engine")

    duration: float = Field(5.0, description="Target duration in seconds")
    width: int = Field(1280, description="Video width")
    height: int = Field(720, description="Video height")
    fps: int = Field(16, description="Frames per second")
    frame_num: int = Field(81, description="Frame count (duration * fps, rounded for the backend)")
    seed: Optional[int] = Field(None, description="Random seed")

    model: Optional[str] = Field(None, description="Per-job model override (else Config.VIDEO_MODEL)")
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Backend-specific parameters, forwarded verbatim in the request body",
    )

    @property
    def size(self) -> str:
        return f"{self.width}x{self.height}"


class VideoJobBatch(BaseModel):
    """All jobs for one scene, in shot order."""

    scene_id: str = Field(..., description="Scene / blueprint ID")
    jobs: List[VideoJob] = Field(default_factory=list)
    total_shots: int = Field(default=0, description="Total number of jobs")
    estimated_duration: float = Field(default=0.0, description="Total estimated duration (seconds)")


# Backward-compatible names (the schema was originally written for Wan 2.2).
WanJob = VideoJob
WanJobBatch = VideoJobBatch

__all__ = ["VideoJob", "VideoJobBatch", "WanJob", "WanJobBatch", "DEFAULT_NEGATIVE_PROMPT"]
