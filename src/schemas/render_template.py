# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
LLM output schema for the TechnicalDirectorAgent (Step 1, template stage)
=========================================================================

The LLM only generates templates containing <asset_id> placeholders; it performs
no string substitution. The final resolved_t2i / resolved_ti2i / resolved_i2v are
assembled by code in Step 2.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class ShotRenderTemplate(BaseModel):
    """Render template for a single shot (LLM output)."""

    shot_id: str = Field(..., description="Shot ID corresponding to the staging_layer")

    # ── Character info ────────────────────────────────────────────────
    characters_in_shot: List[str] = Field(
        default_factory=list,
        description=(
            "Ordered list of visible-character asset_ids in this shot; "
            "the order is the binding order of Picture 1, Picture 2, …. "
            "Use [] for pure-environment shots."
        ),
    )
    character_appearances: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Appearance description of each visible character in this shot, key=asset_id. "
            "Descriptions must match the scene/time/wardrobe state of this shot; the same character is described differently across scenes."
        ),
    )

    # ── T2I template (first-frame static state) ───────────────────────
    t2i_template: str = Field(
        ...,
        description=(
            "keyframe scene description, using <asset_id> placeholders (do not write Picture N or real character names). "
            "Describes the instant before the action begins (T = 0 frame), i.e. the static state before the dramatic action. "
            "Structure: [Style] + [Lighting] + [<asset_id> position and pose] + [gaze/power relations] + [Environment]"
        ),
    )

    # ── I2V template (motion process) ─────────────────────────────────
    i2v_template: str = Field(
        ...,
        description=(
            "Motion-description template, using <asset_id> placeholders. "
            "Describes the action and its aftermath (T > 0). "
            "Structure: [Camera Move] + [<asset_id> actions and interactions] + [lip-sync constraints] + [environmental motion]"
        ),
    )

    # ── Technical note ────────────────────────────────────────────────
    rationale: Optional[str] = Field(
        None,
        description="Director's note: why this visual approach was chosen (shot logic / emotional-match rationale)",
    )


class ShotRenderTemplateList(BaseModel):
    """The final LLM output of the TechnicalDirectorAgent."""

    shots: List[ShotRenderTemplate] = Field(
        default_factory=list,
        description="List of render templates, one-to-one with blueprint.shots",
    )
