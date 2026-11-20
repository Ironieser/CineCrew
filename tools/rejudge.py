#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
rejudge: re-run the VisualJudge on the clips a run already has (every attempt of the listed shots), without
generating anything. Use after changing visual_judge.yaml to check the judge on known footage, and to pick the best
existing attempt. Appends the verdicts (marked "rejudge": true) and points the shot at the best-scoring attempt.

  python tools/rejudge.py <run_dir> --only shot_05,shot_08
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.adapters.media_tools import sample_frames  # noqa: E402
from src.agents.dailies_reviewer.visual_judge import VisualJudgeAgent  # noqa: E402
from src.schemas.blueprint import SceneBlueprint  # noqa: E402


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("run_dir"); ap.add_argument("--only", required=True)
    a = ap.parse_args()
    run = Path(a.run_dir); only = [x for x in a.only.split(",") if x]
    bp_path = run / "shots" / "scene_blueprint_final.json"
    bp = SceneBlueprint.model_validate_json(bp_path.read_text())
    judge = VisualJudgeAgent(); style = bp.global_style or ""
    for shot in bp.shots:
        if not any(shot.shot_id.startswith(o) for o in only) or shot.render_layer is None:
            continue
        clips = sorted((run / "media" / "clips").glob(f"*{shot.shot_id}_*.mp4")) + \
            sorted((run / "media" / "clips").glob(f"retry_*/*{shot.shot_id}_*.mp4"))
        vr = shot.render_layer.visual_review or {}
        prompt = next((x.get("prompt") for c in vr.get("clips", []) for x in c.get("attempts", []) if x.get("prompt")), None) \
            or (shot.render_layer.video.resolved_i2v if shot.render_layer.video else "") or ""
        best = None
        for clip in clips:
            frames = sample_frames(clip, run / "media" / "frames" / "rejudge" / clip.parent.name / clip.stem, n=4)
            r = judge.review_clip([str(f) for f in frames], shot, prompt, style)
            rel = str(clip.relative_to(ROOT)) if str(clip).startswith(str(ROOT)) else str(clip)
            print(f"[rejudge] {shot.shot_id} {clip.parent.name}/{clip.name[-40:]}: {r.score:.2f} {'ok' if r.accepted else 'x'} "
                  f"{'; '.join(r.issues)[:140]}", flush=True)
            vr.setdefault("clips", []).append({"segment_id": f"{shot.shot_id}_rejudge", "attempts": [
                {"attempt": 0, "rejudge": True, "video_path": rel, **r.model_dump()}]})
            if best is None or r.score > best[0]:
                best = (r.score, rel)
        shot.render_layer.visual_review = vr
        if best:
            shot.render_layer.video.video_clip_paths = [best[1]]; shot.render_layer.video.video_clip_path = best[1]
            print(f"[rejudge] {shot.shot_id}: keep {best[1]} ({best[0]:.2f})", flush=True)
    bp_path.write_text(bp.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
