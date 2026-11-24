#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
resume_production: re-run only the ProductionOperator execution stage of an existing run, from its saved
planning artifacts (shots/scene_blueprint_render_filled.json + assets/asset_library.json). Use it after a crash,
an interrupted run, or a backend fix — planning (LLM stages) is not repeated.

  python tools/resume_production.py <run_dir> [--keep shot_01,shot_02 | --only shot_05] [--resync-characters]
                                   [--no-judge] [--max-retries 1]

--keep <prefixes>: shots whose clips already exist in <run_dir>/media/clips are reused (matched by shot_id
prefix), everything else is regenerated. --only <prefixes>: regenerate just these shots and reuse every other
existing clip. --resync-characters: re-derive characters_in_shot + reference conditioning from the staging layer
(technical_director.visible_characters) before rendering — fixes plans made before that guard existed. Stage options (segment_dialogue, judge, max_retries, keyframes)
default to the production_operator entry of PIPELINE_SETTINGS / configs/pipeline_settings.yaml.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Re-execute a run with the settings it was planned with (<run>/pipeline_settings.yaml, written by run_pipeline),
# unless PIPELINE_SETTINGS is given explicitly. Must happen before src.pipeline is imported.
import os  # noqa: E402
_run_arg = next((x for x in sys.argv[1:] if not x.startswith("-") and (Path(x) / "shots").is_dir()), None)
if _run_arg and not os.environ.get("PIPELINE_SETTINGS") and (Path(_run_arg) / "pipeline_settings.yaml").exists():
    os.environ["PIPELINE_SETTINGS"] = str((Path(_run_arg) / "pipeline_settings.yaml").resolve())

from src.agents.production_operator import ProductionOperatorAgent  # noqa: E402
from src.pipeline import load_pipeline_config  # noqa: E402
from src.schemas.assets import AssetLibrary  # noqa: E402
from src.schemas.blueprint import SceneBlueprint  # noqa: E402
from src.schemas.video_jobs import VideoJobBatch  # noqa: E402


def stage_opts() -> dict:
    for spec in load_pipeline_config().get("pipeline", {}).get("stages", []) or []:
        if isinstance(spec, dict) and spec.get("id") == "production_operator":
            return spec
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--keep", default="", help="comma-separated shot_id prefixes whose existing clips are reused")
    ap.add_argument("--only", default="", help="comma-separated shot_id prefixes to regenerate; all other clips reused")
    ap.add_argument("--resync-characters", action="store_true")
    ap.add_argument("--tier", default=None, choices=["draft", "final"],
                    help="final: render on the full-schedule H3 replicas (no turbo LoRA)")
    ap.add_argument("--repair", default=None, help="repair plan JSON (src/skills/repair_policy.plan): per-shot prompt "
                                                   "prefix/suffix, seed offset, duration delta, judge prompt")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--max-retries", type=int, default=None)
    a = ap.parse_args()
    run = Path(a.run_dir)
    opts = stage_opts()
    print(f"[resume] settings: {os.environ.get('PIPELINE_SETTINGS', 'configs/pipeline_settings.yaml')} "
          f"(segment_dialogue={opts.get('segment_dialogue', True)})", flush=True)
    bp = SceneBlueprint.model_validate_json((run / "shots" / "scene_blueprint_render_filled.json").read_text())
    lib = AssetLibrary.model_validate_json((run / "assets" / "asset_library.json").read_text())
    if a.resync_characters:
        from src.agents.technical_director.technical_director_agent import TechnicalDirectorAgent, visible_characters
        regen = [k for k in a.only.split(",") if k]
        for shot in bp.shots:
            img = shot.render_layer.image if shot.render_layer else None
            if img is None or (regen and not any(shot.shot_id.startswith(o) for o in regen)):
                continue   # kept clips keep the characters they were generated (and are graded) with
            chars = visible_characters(img.characters_in_shot, shot, lib)
            if chars != list(img.characters_in_shot or []):
                print(f"[resume] {shot.shot_id}: characters {img.characters_in_shot} -> {chars}", flush=True)
            img.characters_in_shot = chars
            img.conditioning = TechnicalDirectorAgent._build_conditioning(None, chars, lib)
    po = ProductionOperatorAgent()
    batch = po.build_from_blueprint(bp, lib, segment_dialogue=opts.get("segment_dialogue", True))

    keep = [k for k in a.keep.split(",") if k]
    only = [k for k in a.only.split(",") if k]
    if only:
        keep = sorted({j.shot_id for j in batch.jobs if not any(j.shot_id.startswith(o) for o in only)})
    clips_dir = run / "media" / "clips"
    kept = {}
    for job in batch.jobs:
        if any(job.shot_id.startswith(k) for k in keep):
            p = clips_dir / f"{job.job_id}.mp4"
            if p.exists():
                kept[job.job_id] = str(p)
    todo = VideoJobBatch(scene_id=batch.scene_id, jobs=[j for j in batch.jobs if j.job_id not in kept])
    # clips the re-rendered jobs already have: a re-render that fails (timeout, backend down) must not lose the shot
    prior = {j.job_id: str(clips_dir / f"{j.job_id}.mp4") for j in todo.jobs if (clips_dir / f"{j.job_id}.mp4").exists()}
    if a.tier:
        for j in todo.jobs:
            j.extra["tier"] = a.tier
    if a.repair:   # regenerate with what QA found, not a blind re-roll of the same prompt and seed
        rp = json.loads(Path(a.repair).read_text())
        for j in todo.jobs:
            r = rp.get(j.shot_id)
            if not r:
                continue
            body = r.get("judge_prompt") or j.prompt
            j.prompt = "\n".join(x for x in (r.get("prefix"), body, r.get("suffix")) if x)
            j.seed = (j.seed or 0) + int(r.get("seed_offset", 0))
            if r.get("duration_delta"):
                j.duration = max(4.0, j.duration + float(r["duration_delta"]))
                j.frame_num = po.calculate_frame_num(j.duration, j.fps)
            print(f"[resume] repair {j.shot_id}: types={r.get('types')} attempt={r.get('attempt')} seed={j.seed}", flush=True)
    print(f"[resume] {len(kept)} clips kept, {len(todo.jobs)} to render", flush=True)

    results = po.execute_jobs(todo, run / "media", blueprint=bp,
                              judge=False if a.no_judge else opts.get("judge", True),
                              max_retries=a.max_retries if a.max_retries is not None else int(opts.get("max_retries", 1)),
                              keyframes=opts.get("keyframes", True), stitch=False,
                              parallel=int(opts.get("parallel", 1)), library=lib,
                              keyframe_retries=opts.get("keyframe_retries"))

    rendered = {r.job_id for r in results if r.video_path}
    for job in todo.jobs:
        if job.job_id not in rendered and job.job_id in prior and Path(prior[job.job_id]).exists():
            kept[job.job_id] = prior[job.job_id]
            print(f"[resume] {job.shot_id}: re-render failed, keeping the previous clip", flush=True)

    # merge kept clips back into the blueprint in shot/segment order, then stitch
    by_shot = {s.shot_id: s for s in bp.shots}
    prev_path = run / "shots" / "scene_blueprint_final.json"
    if prev_path.exists():   # kept shots keep the judge verdicts they were accepted with
        prev = {s.shot_id: s for s in SceneBlueprint.model_validate_json(prev_path.read_text()).shots}
        for sid, shot in by_shot.items():
            p0 = prev.get(sid)
            if (sid in {j.shot_id for j in batch.jobs if j.job_id in kept} and p0 and p0.render_layer
                    and shot.render_layer and not shot.render_layer.visual_review):
                shot.render_layer.visual_review = p0.render_layer.visual_review
    for job in batch.jobs:
        shot = by_shot.get(job.shot_id)
        if job.job_id in kept and shot and shot.render_layer is not None:
            shot.render_layer.video.video_clip_paths = [kept[job.job_id]] + list(shot.render_layer.video.video_clip_paths)
            shot.render_layer.video.video_clip_path = shot.render_layer.video.video_clip_paths[0]
    film = po.stitch(bp, run / "media" / "film.mp4")
    (run / "shots" / "scene_blueprint_final.json").write_text(bp.model_dump_json(indent=2))
    (run / "shots" / "video_results.json").write_text(json.dumps([r.model_dump() for r in results], ensure_ascii=False, indent=1))
    print(f"[resume] film: {film}", flush=True)


if __name__ == "__main__":
    main()
