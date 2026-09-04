# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Intermediate output schemas for each Agent in the Blueprint Pipeline
====================================================================

Each Agent only outputs the list of Layers it is responsible for, and the
pipeline then merges these into the SceneBlueprint.

  StoryEditorAgent     → ShotNarrativeList   (Layer 1: narrative_layer per shot)
  CinematographerAgent → ShotStagingList     (Layer 2: staging_layer per shot)

These two structures are aligned by shot_id by the pipeline and written into
SceneBlueprint.shots.
"""

from pydantic import BaseModel, Field
from typing import List

from .blueprint import NarrativeLayer, StagingLayer


class ShotNarrative(BaseModel):
    """StoryEditorAgent's output for a single shot (Layer 1)."""
    shot_id: str = Field(..., description="Unique shot ID, assigned by the StoryEditorAgent")
    narrative_layer: NarrativeLayer


class ShotNarrativeList(BaseModel):
    """The final output of the StoryEditorAgent."""
    shots: List[ShotNarrative] = Field(
        default_factory=list,
        description="List of narrative shots in chronological order",
    )


class ShotStaging(BaseModel):
    """CinematographerAgent's output for a single shot (Layer 2)."""
    shot_id: str = Field(..., description="Shot ID corresponding to the narrative_layer")
    staging_layer: StagingLayer


class ShotStagingList(BaseModel):
    """The final output of the CinematographerAgent."""
    shots: List[ShotStaging] = Field(
        default_factory=list,
        description="List of shot staging, one-to-one with ShotNarrativeList",
    )
