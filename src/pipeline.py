#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Config-driven pipeline runner (FilmDSL / Blueprint).

Stages are read from configs/pipeline_settings.yaml (pipeline.stages): list order
is execution order, and `enabled: false` skips a stage. Turning an agent on/off or
reordering the pipeline only requires editing the YAML, not Python.

One SceneBlueprint (the FilmDSL document) is threaded through every stage; each
stage reads the current blueprint (+ script_segment / asset_library), fills only
the layer it owns, and writes the updated blueprint back to the context.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .utils.limits_config import get_limits

# Locate the config relative to the project root by default.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "configs" / "pipeline_settings.yaml"


def _save_json(obj: Any, path: Path) -> None:
    """Write a Pydantic model or plain object to JSON (utf-8, pretty)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(obj, "model_dump_json"):
        text = obj.model_dump_json(indent=2)
    else:
        text = json.dumps(obj, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")


def _opt(stage_spec: Any, key: str, default: Any) -> Any:
    """Per-stage option from pipeline_settings.yaml (stage entries may be plain ids)."""
    if isinstance(stage_spec, dict) and stage_spec.get(key) is not None:
        return stage_spec[key]
    return default


def load_pipeline_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configs/pipeline_settings.yaml and return the full config."""
    path = config_path or _CONFIG_PATH
    if not path.exists():
        return {"pipeline": {"stages": []}}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_enabled_stages(config_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Return the enabled entries of pipeline.stages, preserving list order."""
    config = load_pipeline_config(config_path)
    pipeline_cfg = config.get("pipeline", {})
    stages = pipeline_cfg.get("stages", [])
    if isinstance(stages, dict):
        return [{"id": k, "enabled": v} for k, v in stages.items() if v]
    return [s for s in stages if s.get("enabled", True)]


def run_pipeline(
    script_content: str,
    *,
    stages: Optional[List[Dict[str, Any]]] = None,
    config_path: Optional[Path] = None,
    script_segment_max_len: Optional[int] = None,
    enable_hallucination_guard: bool = True,
    dsl_validator_auto_correct: bool = True,
    session_id: Optional[str] = None,
    run_root: Optional[Path] = None,
    initial_ctx: Optional[Dict[str, Any]] = None,
    reuse_trace: bool = False,
) -> Dict[str, Any]:
    """
    Execute the pipeline stages in configured order.

    A single SceneBlueprint is filled layer by layer:
        ArtDepartment      -> metadata + global_style + AssetLibrary
        StoryEditor        -> shots[].narrative_layer  (Layer 1)
        Cinematographer    -> shots[].staging_layer    (Layer 2)
        DSLValidator       -> validate staging_layer entity IDs
        VODirector         -> shots[].narrative_layer.dialogue + performance emotion
        TechnicalDirector  -> shots[].render_layer      (Layer 3)
        DailiesReviewer    -> refines resolved prompts (closed loop)
        ProductionOperator -> shots[].assembly_layer (Layer 4) + VideoJobBatch
                              (+ execute: true -> keyframes/clips with VLM judge)

    Per-stage options come from the stage entry in pipeline_settings.yaml (see that file).

    Args:
        stages: if None, read from the config file.
        run_root: when set, this run's assets/shots/logs are written under it.
        initial_ctx: callers may pre-fill part of the context (e.g. inject an
            asset_library / scene_blueprint produced by an external ArtDepartment run).
        reuse_trace: keep the trace the caller already opened (so spans logged before
            run_pipeline — e.g. the Art Department in run_dataset_story — share the
            same trace id, span numbering and logs/ directory).
    """
    from .utils.agent_trace import new_trace, get_trace_id, write_index, set_trace_output_dir, get_current_trace_dir

    trace_id = get_trace_id() if (reuse_trace and get_trace_id()) else new_trace(session_id=session_id)
    if run_root is not None:
        run_root = Path(run_root)
        (run_root / "logs").mkdir(parents=True, exist_ok=True)
        set_trace_output_dir(run_root / "logs")

    from .agents.art_department import ArtDepartmentAgent
    from .agents.story_editor import StoryEditorAgent
    from .agents.cinematographer import CinematographerAgent
    from .agents.dsl_validator import DSLValidatorAgent
    from .agents.vo_director import VODirectorAgent
    from .agents.technical_director import TechnicalDirectorAgent
    from .agents.dailies_reviewer import DailiesReviewerAgent
    from .agents.production_operator import ProductionOperatorAgent
    from .schemas.blueprint import SceneBlueprint

    if stages is None:
        stages = get_enabled_stages(config_path)
    if not stages:
        raise ValueError("No enabled pipeline stages. Check configs/pipeline_settings.yaml pipeline.stages.")

    # Ordering guard: dailies_reviewer refines resolved prompts in place; those refinements
    # only reach the VideoJobBatch if production_operator runs AFTER it. Warn if that invariant
    # is violated (production_operator missing, or ordered before dailies_reviewer).
    _stage_ids = [str(s.get("id") if isinstance(s, dict) else s).strip() for s in stages]
    if "dailies_reviewer" in _stage_ids:
        if "production_operator" not in _stage_ids:
            print(
                "   ⚠️  [Pipeline] dailies_reviewer is enabled but production_operator is not; "
                "the refined prompts will not reach any VideoJobBatch.",
                flush=True,
            )
        elif _stage_ids.index("production_operator") < _stage_ids.index("dailies_reviewer"):
            print(
                "   ⚠️  [Pipeline] production_operator runs BEFORE dailies_reviewer; "
                "the VideoJobBatch will be built from un-refined prompts.",
                flush=True,
            )

    if script_segment_max_len is None:
        script_segment_max_len = get_limits(config_path).get("script_segment_dsl", 10000)

    ctx: Dict[str, Any] = {
        "script_content": script_content,
        "script_segment": script_content[:script_segment_max_len]
        if len(script_content) > script_segment_max_len
        else script_content,
        "asset_library": None,
        "scene_blueprint": None,
        "video_jobs": None,
        "video_results": None,
        "validation_report": None,
        "dailies_report": None,
        "trace_id": trace_id,
        "run_root": run_root,
    }
    # Callers may pre-fill context (e.g. inject an asset_library produced externally).
    if initial_ctx:
        ctx.update({k: v for k, v in initial_ctx.items() if v is not None})

    _shots_dir = (run_root / "shots") if run_root is not None else (_PROJECT_ROOT / "data" / "output" / "shots")
    _assets_base = str(run_root / "assets") if run_root is not None else "data/output/assets"

    for stage_spec in stages:
        stage_id = (stage_spec.get("id") if isinstance(stage_spec, dict) else stage_spec)
        if stage_id is None:
            continue
        stage_id = str(stage_id).strip()
        if not stage_id:
            continue

        # ── Stage 1: ArtDepartment → AssetLibrary + init SceneBlueprint ──────────
        if stage_id == "art_department":
            print(f"\n--- [Pipeline] STAGE 1: ArtDepartment [trace_id={trace_id}] ---", flush=True)
            w = ArtDepartmentAgent()
            ctx["asset_library"] = w.run(
                ctx["script_content"],
                enable_hallucination_guard=enable_hallucination_guard,
                base_path=_assets_base,
                generate_references=_opt(stage_spec, "generate_references", False),
            )
            if ctx["asset_library"] is not None:
                import uuid
                ctx["scene_blueprint"] = SceneBlueprint.from_asset_library(
                    ctx["asset_library"],
                    blueprint_id=f"blueprint_{uuid.uuid4().hex[:8]}",
                )
                print(
                    f"   ✅ SceneBlueprint initialized: id={ctx['scene_blueprint'].blueprint_id}",
                    flush=True,
                )

        # ── Stage 2a: StoryEditor → shots[].narrative_layer (Layer 1) ────────────
        elif stage_id == "story_editor":
            if ctx["asset_library"] is None:
                raise RuntimeError("story_editor requires asset_library.")
            print("\n--- [Pipeline] STAGE 2a: StoryEditor → narrative_layer ---", flush=True)
            na = StoryEditorAgent()
            ctx["scene_blueprint"] = na.run(
                ctx["script_segment"],
                ctx["asset_library"],
                blueprint=ctx.get("scene_blueprint"),
            )

        # ── Stage 2b: Cinematographer → shots[].staging_layer (Layer 2) ──────────
        elif stage_id == "cinematographer":
            if ctx["scene_blueprint"] is None:
                raise RuntimeError(
                    "cinematographer requires scene_blueprint with narrative_layer filled; "
                    "enable story_editor first."
                )
            if ctx["asset_library"] is None:
                raise RuntimeError("cinematographer requires asset_library.")
            print("\n--- [Pipeline] STAGE 2b: Cinematographer → staging_layer ---", flush=True)
            cine = CinematographerAgent()
            ctx["scene_blueprint"] = cine.run(ctx["scene_blueprint"], ctx["asset_library"])

        # ── Stage 2.5: DSLValidator → validate staging_layer entity IDs ──────────
        elif stage_id == "dsl_validator":
            print("\n--- [Pipeline] STAGE 2.5: DSLValidator ---", flush=True)
            if ctx["asset_library"] is None:
                raise RuntimeError("dsl_validator requires asset_library.")
            if ctx["scene_blueprint"] is None:
                raise RuntimeError("dsl_validator requires scene_blueprint.")
            v = DSLValidatorAgent()
            auto_correct = _opt(stage_spec, "auto_correct", dsl_validator_auto_correct)
            ctx["scene_blueprint"], ctx["validation_report"] = v.run(
                ctx["scene_blueprint"], ctx["asset_library"], auto_correct=auto_correct
            )
            _save_json(ctx["validation_report"], _shots_dir / "validation_report.json")

        # ── Stage 3: VODirector → shots[].narrative_layer.dialogue ───────────────
        elif stage_id == "vo_director":
            if ctx["asset_library"] is None:
                raise RuntimeError("vo_director requires asset_library.")
            if ctx["scene_blueprint"] is None:
                raise RuntimeError("vo_director requires scene_blueprint.")
            print("\n--- [Pipeline] STAGE 3: VODirector → narrative_layer.dialogue + performance ---", flush=True)
            da = VODirectorAgent()
            design_voices = _opt(stage_spec, "design_voices", False)
            ctx["scene_blueprint"] = da.run_on_blueprint(
                ctx["scene_blueprint"],
                ctx["script_segment"],
                ctx["asset_library"],
                infer_emotion=_opt(stage_spec, "infer_emotion", True),
                design_voices=design_voices,
            )
            if design_voices:
                from .skills.asset_management import save_assets
                save_assets(ctx["asset_library"], _assets_base)  # persist CharacterAsset.voice_design

        # ── Stage 4: TechnicalDirector → shots[].render_layer (Layer 3) ──────────
        elif stage_id == "technical_director":
            if ctx["scene_blueprint"] is None:
                raise RuntimeError("technical_director requires scene_blueprint.")
            if ctx["asset_library"] is None:
                raise RuntimeError("technical_director requires asset_library.")
            print("\n--- [Pipeline] STAGE 4: TechnicalDirector → render_layer ---", flush=True)
            rb = TechnicalDirectorAgent()
            ctx["scene_blueprint"] = rb.run(ctx["scene_blueprint"], ctx["asset_library"])

            bp_path = _shots_dir / "scene_blueprint_render_filled.json"
            _save_json(ctx["scene_blueprint"], bp_path)
            print(f"   ✅ Saved Blueprint (render filled): {bp_path}", flush=True)

        # ── Stage 4.5: DailiesReviewer → closed-loop refinement of resolved prompts ──
        elif stage_id == "dailies_reviewer":
            if ctx["scene_blueprint"] is None:
                raise RuntimeError("dailies_reviewer requires scene_blueprint.")
            print("\n--- [Pipeline] STAGE 4.5: DailiesReviewer → refine resolved prompts ---", flush=True)
            dr = DailiesReviewerAgent()
            # max_rounds is configurable per-stage in pipeline_settings.yaml (defaults to the agent's own default).
            dr_kwargs = {}
            if _opt(stage_spec, "max_rounds", None) is not None:
                dr_kwargs["max_rounds"] = int(_opt(stage_spec, "max_rounds", None))
            ctx["scene_blueprint"], ctx["dailies_report"] = dr.run(
                ctx["scene_blueprint"], ctx["asset_library"], **dr_kwargs
            )
            _save_json(ctx["dailies_report"], _shots_dir / "dailies_report.json")
            print(
                f"   ✅ DailiesReviewer: {ctx['dailies_report']['total_fixed']} change(s) "
                f"over {ctx['dailies_report']['total_rounds']} round(s)"
                + (f", {ctx['dailies_report']['total_errored']} errored"
                   if ctx['dailies_report']['total_errored'] else ""),
                flush=True,
            )

        # ── Stage 5: ProductionOperator → assembly_layer (Layer 4) + VideoJobBatch ──
        elif stage_id == "production_operator":
            if ctx["asset_library"] is None:
                raise RuntimeError("production_operator requires asset_library.")
            if ctx["scene_blueprint"] is None:
                raise RuntimeError("production_operator requires scene_blueprint.")
            print("\n--- [Pipeline] STAGE 5: ProductionOperator → assembly_layer + VideoJobBatch ---", flush=True)
            wa = ProductionOperatorAgent()
            ctx["video_jobs"] = wa.build_from_blueprint(ctx["scene_blueprint"], ctx["asset_library"])
            _save_json(ctx["video_jobs"], _shots_dir / "video_jobs.json")

            # Opt-in execution (`execute: true` on this stage): keyframes via T2I_*, clips via
            # VIDEO_*, each gated by the VLM VisualJudge with retries; paths/verdicts land in the blueprint.
            if _opt(stage_spec, "execute", False):
                _media_dir = (run_root / "media") if run_root is not None else (_PROJECT_ROOT / "data" / "output" / "media")
                ctx["video_results"] = wa.execute_jobs(
                    ctx["video_jobs"],
                    _media_dir,
                    blueprint=ctx["scene_blueprint"],
                    judge=_opt(stage_spec, "judge", True),
                    max_retries=int(_opt(stage_spec, "max_retries", 1)),
                    keyframes=_opt(stage_spec, "keyframes", True),
                    stitch=_opt(stage_spec, "stitch", True),
                )
                _save_json(ctx["video_jobs"], _shots_dir / "video_jobs.json")  # prompts as finally rendered
                _save_json([r.model_dump() for r in ctx["video_results"]], _shots_dir / "video_results.json")

            final_bp_path = _shots_dir / "scene_blueprint_final.json"
            _save_json(ctx["scene_blueprint"], final_bp_path)
            print(f"   ✅ Saved final Blueprint (all layers): {final_bp_path}", flush=True)

        else:
            print(f"   ⚠️  Unknown stage id: {stage_id!r}, skipping.", flush=True)

    write_index()
    if trace_id:
        trace_dir = get_current_trace_dir()
        if trace_dir:
            print(f"\n   📁 Trace logs: {trace_dir}/", flush=True)
    return ctx
