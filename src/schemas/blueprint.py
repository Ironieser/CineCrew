# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
SceneBlueprint — Four-layer orthogonal DSL (the single evolving artifact of the Pipeline)
=========================================================================================

DSL-centric design: each Pipeline Agent only reads from and writes to this DSL,
progressively refining the same Blueprint. See DEV_NOTES.md.

Design principle:
  Each layer is written by exactly one responsible Agent; other Agents do not
  modify it out of turn:

  Layer 0 — metadata, global_style  ← ArtDepartment (initialized via AssetLibrary)
  Layer 1 — narrative_layer         ← StoryEditor (initial fill) + VODirector (dialogue refinement)
  Layer 2 — staging_layer           ← Cinematographer (fill) + DSLValidator (validation)
  Layer 3 — render_layer            ← TechnicalDirector (+ DailiesReviewer refinement)
  Layer 4 — assembly_layer          ← ProductionOperator

Layers 2/3/4 may be None early in the generation chain and are filled in by the
corresponding Agent in Stage order.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

from .assets import AssetLibrary


# ─────────────────────────────────────────────
# Layer 1: Narrative Layer
# Owner: StoryEditorAgent (initial) + VODirector (dialogue refinement)
# ─────────────────────────────────────────────

class DialogueDef(BaseModel):
    has_dialogue: bool = False
    speaker_asset_id: Optional[str] = Field(
        None, description="char_xxx ID in the AssetLibrary"
    )
    listener_asset_id: Optional[str] = Field(
        None, description="Primary listener char_xxx ID or 'group'"
    )
    text: Optional[str] = Field(None, description="Verbatim dialogue line")
    voice_preset: Optional[str] = Field(
        None, description="TTS voice preset ID"
    )


class NarrativeLayer(BaseModel):
    narrative_action: str = Field(
        ..., description="The main action in this shot, summarized in one sentence"
    )
    emotional_beat: str = Field(
        ..., description="Emotional-arc label"
    )
    dialogue: DialogueDef = Field(
        default_factory=DialogueDef,
        description="Dialogue definition; remaining fields are ignored when has_dialogue=False",
    )
    # Acting direction, filled by VODirector (the paper's Acting Coach): the performed
    # emotional state at this moment, inferred from the line + speaker persona + staging
    # (or from the visuals alone on silent shots). Complements the editorial emotional_beat.
    performance_emotion: Optional[str] = Field(
        None, description="Performed emotion label, e.g. 'restrained rage', 'melancholic hope'"
    )
    performance_intensity: Optional[int] = Field(
        None, ge=1, le=10, description="Intensity of performance_emotion, 1-10"
    )


# ─────────────────────────────────────────────
# Layer 2: Staging Layer
# Owner: CinematographerAgent + DSLValidatorAgent (validates entity IDs)
# ─────────────────────────────────────────────

class CameraSpec(BaseModel):
    shot_scale: Optional[
        Literal["ECU", "CU", "MCU", "MS", "MLS", "LS", "ELS", "OTS", "POV"]
    ] = Field(None, description="Shot-scale type")
    angle: Optional[
        Literal["eye_level", "low", "high", "dutch", "overhead", "undershot"]
    ] = Field(None, description="Camera angle")
    movement: Optional[str] = Field(
        None, description="Camera-movement description, e.g. 'slow_dolly_in', 'static'"
    )


class EntityInStaging(BaseModel):
    asset_id: str = Field(..., description="ID from the AssetLibrary")
    position: Optional[str] = Field(None, description="Composition position")
    action_state: Optional[str] = Field(None, description="Pose / action state")


class StagingLayer(BaseModel):
    duration_seconds: float = Field(..., gt=0.0, description="Target duration of this shot (seconds)")
    camera: CameraSpec = Field(default_factory=CameraSpec)
    lighting: Optional[str] = Field(None, description="Semantic label for the lighting scheme")
    environment_id: Optional[str] = Field(
        None, description="Location ID, from AssetLibrary.locations.id"
    )
    entities: List[EntityInStaging] = Field(
        default_factory=list, description="Entities present in the frame and their staging info"
    )
    consistency_constraints: List[str] = Field(
        default_factory=list, description="Hard visual constraints for the Critic to check"
    )


# ─────────────────────────────────────────────
# Layer 3: Render Layer
# Owner: TechnicalDirectorAgent
#
# Design: two-stage separation
#   Stage 1 (LLM generation):
#     - t2i_template    : first-frame static-state description (before action begins), with <asset_id> placeholders
#     - i2v_template    : motion description (during and after the action), with <asset_id> placeholders
#     - characters_in_shot  : list of character asset_ids in this shot (determines Picture 1/2/3 order)
#     - character_appearances: each character's appearance in this shot (scene/wardrobe/pose related)
#   Stage 2 (code assembly via VisualPromptTranslatorAgent):
#     - resolved_t2i    : final T2I prompt (when no reference image)
#     - resolved_ti2i   : final Ti2I prompt (when reference images exist, prefixed "Picture 1 is ...")
#     - resolved_i2v    : final I2V prompt (<asset_id> replaced by appearance descriptions)
# ─────────────────────────────────────────────

class CharacterConsistencyControl(BaseModel):
    asset_id: str
    method: str = Field("ip_adapter_faceid")
    reference_image_paths: List[str] = Field(default_factory=list)
    weight: float = Field(0.85, ge=0.0, le=1.0)


class ConditioningSpec(BaseModel):
    character_consistency: List[CharacterConsistencyControl] = Field(
        default_factory=list
    )


class ImageRenderSpec(BaseModel):
    """
    First-frame (T2I / Ti2I) generation spec.

    LLM stage (TechnicalDirectorAgent Step 1) fills:
      - t2i_template         : keyframe prompt template, with <asset_id>
      - characters_in_shot   : ordered list of characters present (determines Picture N order)
      - character_appearances : appearance description of each character in this shot (Chinese or English)

    Assembly stage (VisualPromptTranslatorAgent / Step 2) fills:
      - resolved_t2i   : final prompt when no reference image (<asset_id> replaced)
      - resolved_ti2i  : final prompt when reference images exist (Picture N prefix + replacement)
    """
    engine: str = Field("", description="T2I model that renders this keyframe (Config.T2I_MODEL)")

    # ── LLM generation (template, with placeholders) ──
    t2i_template: Optional[str] = Field(
        None,
        description="keyframe scene description, <asset_id> placeholders, describing the static state before the action begins",
    )
    characters_in_shot: List[str] = Field(
        default_factory=list,
        description="ordered list of visible-character asset_ids in this shot (by composition order → Picture 1,2,3…)",
    )
    character_appearances: Dict[str, str] = Field(
        default_factory=dict,
        description="appearance description of each character in this shot, key=asset_id, value=wardrobe/pose/scene description",
    )

    # ── Code assembly (resolved, no placeholders) ──
    resolved_t2i: Optional[str] = Field(
        None, description="final T2I prompt (used when no reference-image path)"
    )
    resolved_ti2i: Optional[str] = Field(
        None, description="final Ti2I prompt (used when reference-image paths exist, includes Picture N prefix)"
    )

    # ── Generated artifact ──
    # Filled by ProductionOperatorAgent.execute_jobs() (T2IClient, OpenAI-style
    # /images API) when execution is enabled; None while the blueprint is a plan only.
    keyframe_image_path: Optional[str] = Field(
        None, description="Path to the generated keyframe image (None until the T2I backend has run)."
    )

    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    conditioning: Optional[ConditioningSpec] = None
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class VideoEngineParams(BaseModel):
    resolution: Optional[str] = None
    fps: Optional[int] = None
    camera_motion_intensity: Optional[float] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class LipSyncConstraint(BaseModel):
    enabled: bool = False
    sync_method: Optional[str] = None
    audio_source_ref: Optional[str] = None


class VideoRenderSpec(BaseModel):
    """
    Video (I2V / T2V) generation spec.

    LLM stage (TechnicalDirectorAgent Step 1) fills:
      - i2v_template : motion-description template, with <asset_id>, describing the action and its aftermath

    Assembly stage (VisualPromptTranslatorAgent / Step 2) fills:
      - resolved_i2v : final I2V prompt (<asset_id> replaced by character_appearances)
    """
    engine: str = Field("", description="Video model that renders this clip (Config.VIDEO_MODEL)")

    # ── LLM generation (template, with placeholders) ──
    i2v_template: Optional[str] = Field(
        None,
        description=(
            "motion-description template, <asset_id> placeholders; "
            "describes: [Camera Move] + [character actions and interactions] + [lip-sync constraints] + [environmental motion]"
        ),
    )

    # ── Code assembly (resolved, no placeholders) ──
    resolved_i2v: Optional[str] = Field(
        None, description="final I2V prompt (after <asset_id> replacement)"
    )

    # ── Generated artifact ──
    # Filled by ProductionOperatorAgent.execute_jobs() (src/adapters/video_client.py,
    # OpenAI-style /videos API) when execution is enabled; otherwise stays None and the
    # VideoJobBatch is the executable spec.
    video_clip_path: Optional[str] = Field(
        None,
        description="Path to the generated clip (first segment when the shot was split; None until executed).",
    )
    video_clip_paths: List[str] = Field(
        default_factory=list,
        description="All generated clips of this shot in playback order (one per VideoJob segment).",
    )

    engine_params: VideoEngineParams = Field(default_factory=VideoEngineParams)
    lip_sync_constraint: LipSyncConstraint = Field(
        default_factory=LipSyncConstraint
    )


class RenderLayer(BaseModel):
    image: ImageRenderSpec = Field(default_factory=ImageRenderSpec)
    video: VideoRenderSpec = Field(default_factory=VideoRenderSpec)

    # Two-stage QA: DailiesReviewer critiques the *prompts* before rendering; during
    # execution VisualJudgeAgent (VLM) scores the *generated media* and drives retries.
    visual_review: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "VLM judge verdicts from execution: {keyframe: VisualReview, clips: [VisualReview...], "
            "attempts: {...}}. None until execute: true has run."
        ),
    )


# ─────────────────────────────────────────────
# Layer 4: Assembly Layer
# Owner: ProductionOperatorAgent / post-production assembly flow
# ─────────────────────────────────────────────

class AudioTrack(BaseModel):
    track_id: str
    type: Literal["dialogue", "sfx", "bgm", "narration"] = "dialogue"
    source: Optional[str] = Field(None, description="Voice preset / generator id")
    description: Optional[str] = Field(None, description="The line (dialogue) or a cue (bgm / sfx)")


class AssemblyLayer(BaseModel):
    transition_in: str = Field("cut")
    transition_out: str = Field("cut")
    audio_tracks: List[AudioTrack] = Field(default_factory=list)


# ─────────────────────────────────────────────
# Top-level Blueprint
# ─────────────────────────────────────────────

class ShotBlueprint(BaseModel):
    """
    Four-layer Blueprint for a single shot.

    render_layer / assembly_layer may be None after the narrative/staging layers
    are written, and are filled in by downstream Agents in order.
    """
    shot_id: str = Field(..., description="Unique shot ID")

    # Layer 1: filled by StoryEditorAgent (None initially; required after that Agent runs)
    narrative_layer: Optional[NarrativeLayer] = None

    # Layer 2: filled by CinematographerAgent (None initially)
    staging_layer: Optional[StagingLayer] = None

    # Layer 3: filled by TechnicalDirectorAgent (None initially)
    render_layer: Optional[RenderLayer] = None

    # Layer 4: filled by the post-production flow (None initially)
    assembly_layer: Optional[AssemblyLayer] = None

    def ensure_render_layer(self) -> RenderLayer:
        """Get or initialize render_layer."""
        if self.render_layer is None:
            self.render_layer = RenderLayer()
        return self.render_layer

    def summary_dict(self) -> Dict[str, Any]:
        """Compact, JSON-serialisable summary of this shot for LLM context
        (narrative + staging + resolved render prompts). Single source of truth
        so callers don't re-implement nested-layer extraction."""
        narrative = self.narrative_layer
        staging = self.staging_layer
        render = self.render_layer
        return {
            "shot_id": self.shot_id,
            "narrative_action": narrative.narrative_action if narrative else "",
            "emotional_beat": narrative.emotional_beat if narrative else "",
            "duration_seconds": staging.duration_seconds if staging else None,
            "camera": staging.camera.model_dump() if (staging and staging.camera) else {},
            "entities": [e.model_dump() for e in staging.entities] if (staging and staging.entities) else [],
            "resolved_t2i": render.image.resolved_t2i if render else None,
            "resolved_ti2i": render.image.resolved_ti2i if render else None,
            "resolved_i2v": render.video.resolved_i2v if render else None,
        }

    def ensure_assembly_layer(self) -> AssemblyLayer:
        """Get or initialize assembly_layer."""
        if self.assembly_layer is None:
            self.assembly_layer = AssemblyLayer()
        return self.assembly_layer


class BlueprintMetadata(BaseModel):
    """Layer 0 — project metadata; render targets come from Config (VIDEO_SIZE / VIDEO_FPS)."""
    project_name: str
    target_resolution: str = "1280x720"
    target_aspect_ratio: str = "16:9"
    global_fps: int = 16


class SceneBlueprint(BaseModel):
    """
    Scene-level Blueprint: a unified DSL container written to in cascade by each Agent.

    Lifecycle:
      1. ArtDepartmentAgent   → from_asset_library() initializes metadata + global_style
      2. StoryEditorAgent     → writes each shot's narrative_layer
      3. CinematographerAgent → writes each shot's staging_layer
      4. DSLValidatorAgent    → validates staging_layer entity IDs
      5. VODirectorAgent      → refines narrative_layer.dialogue
      6. TechnicalDirectorAgent → fills render_layer (T2I + T2V resolved prompts)
      7. DailiesReviewerAgent → closed-loop refinement of resolved prompts
      8. ProductionOperatorAgent → reads render_layer, builds VideoJobBatch + assembly_layer
    """
    blueprint_id: str = Field(..., description="Globally unique ID")
    metadata: BlueprintMetadata
    global_style: str = Field(..., description="Global visual style, from the AssetLibrary")
    final_film_path: Optional[str] = Field(
        None, description="The assembled film (all clips cut together), once execution has run with stitch: true"
    )
    shots: List[ShotBlueprint] = Field(default_factory=list)

    @classmethod
    def from_asset_library(
        cls,
        asset_library: "AssetLibrary",
        blueprint_id: str,
    ) -> "SceneBlueprint":
        """
        Layer 0: initialize a blank Blueprint from the AssetLibrary (project name, global
        style) and the configured render target (VIDEO_SIZE / VIDEO_FPS). shots stays
        empty until the StoryEditorAgent runs.
        """
        from ..config import Config

        return cls(
            blueprint_id=blueprint_id,
            metadata=BlueprintMetadata(
                project_name=asset_library.project_title,
                target_resolution=Config.VIDEO_SIZE,
                target_aspect_ratio=_aspect_ratio(Config.VIDEO_SIZE),
                global_fps=Config.VIDEO_FPS,
            ),
            global_style=asset_library.global_style,
            shots=[],
        )


def _aspect_ratio(size: str) -> str:
    """'1280x720' -> '16:9'."""
    try:
        from math import gcd
        w, h = (int(v) for v in size.lower().replace("*", "x").split("x"))
        g = gcd(w, h)
        return f"{w // g}:{h // g}"
    except Exception:
        return "16:9"
