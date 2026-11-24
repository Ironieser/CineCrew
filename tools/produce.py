#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
produce: hands-off story -> finished film loop.

  python tools/produce.py <story_dir> [--hint "ASR domain words"] [--rounds 2] [--run <existing run_dir>]

  1. plan + render with run_dataset_story.py (PIPELINE_SETTINGS, default configs/pipeline_settings_h3.yaml)
  2. qa_report  -> shots failing a shot-level gate (ASR, dead air, judge, VLM) are regenerated with
     resume_production --only <failed> --resync-characters; repeat up to --rounds times
  3. post_production -> media/film_post.mp4, then qa_report --post
Writes <run>/produce_log.json (gates per round, regenerated shots, wall time) for stability statistics.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
# dead air is not a reason to regenerate: post_production trims it (it is still graded on the post film)
# hard gates only (calibrated on data/calib); judge / generic VLM verdicts are advisory
SHOT_GATES = ("audio.asr", "visual.continuity", "visual.text", "visual.identity", "visual.world", "visual.presence",
              "visual.action", "visual.cut")


def sh(*args, env=None):
    print("[produce] $", " ".join(str(a) for a in args), flush=True)
    subprocess.run([str(a) for a in args], check=True, cwd=ROOT, env=env)


def _dotenv_has(prefix: str) -> bool:
    p = ROOT / ".env"
    return p.exists() and any(l.strip().startswith(prefix) and "=" in l and l.split("=", 1)[1].strip()
                              for l in p.read_text().splitlines())


def qa(run: Path, hint: str, post=False) -> dict:
    sh("python3", "tools/qa_report.py", run, "--hint", hint, *(["--post"] if post else []))
    rep = json.loads((run / ("qa_report_post.json" if post else "qa_report.json")).read_text())
    if rep.get("vlm_errors"):   # a checker that crashed must not read as a pass
        sys.exit(f"[produce] the VLM check failed on {rep['vlm_errors']} shot(s) (see vlm_error in the report); "
                 "fix the checker or the LLM endpoint before trusting this round")
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story", nargs="?", default=None, help="story dir (script_synopsis.json); omit with --from-source")
    ap.add_argument("--hint", default=""); ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--final-max", type=int, default=3, help="shots re-rendered on the final tier (closing shot first)")
    ap.add_argument("--from-source", default=None, help="adapt this source text first (novel excerpt / science topic)")
    ap.add_argument("--kind", default="novel excerpt"); ap.add_argument("--seconds", type=int, default=60)
    ap.add_argument("--run", default=None, help="continue from an already rendered run directory")
    a = ap.parse_args()
    env = dict(os.environ); env.setdefault("PIPELINE_SETTINGS", str(ROOT / "configs" / "pipeline_settings_h3.yaml"))
    t0 = time.time()
    if a.from_source:   # source material -> filmable script (ScreenwriterAgent) -> our_dataset/<Story>
        sys.path.insert(0, str(ROOT))
        from src.agents.screenwriter import ScreenwriterAgent
        sp = ScreenwriterAgent().write(Path(a.from_source).read_text(), kind=a.kind, seconds=a.seconds)
        a.story = str(ScreenwriterAgent.save(sp, ROOT / "our_dataset"))
        print(f"[produce] adapted '{sp.title}' -> {a.story}", flush=True)
    if not a.story:
        sys.exit("[produce] give a story directory or --from-source")
    log = {"story": a.story, "rounds": []}
    story = Path(a.story)
    if a.run:
        run = Path(a.run)
    else:
        sh(PY, "run_dataset_story.py", story, "--execute", env=env)
        runs = sorted((ROOT / "data" / "runs" / "dataset" / story.name).glob("*/"), key=lambda p: p.stat().st_mtime)
        run = runs[-1]
    log["run"] = str(run); log["render_s"] = round(time.time() - t0)
    lib = json.loads((run / "assets" / "asset_library.json").read_text())
    missing = [c["id"] for c in lib.get("characters", [])
               if not ((c.get("visual_references") or {}).get("canonical_image_path"))]
    if missing:   # identity has no anchor: every later shot would drift, so stop instead of producing a weak film
        sys.exit(f"[produce] characters without a reference image: {missing} (check T2I_* / generate_references)")
    sys.path.insert(0, str(ROOT))
    from src.skills.repair_policy import plan as repair_plan
    for rnd in range(a.rounds + 1):
        rep = qa(run, a.hint)
        flagged = sorted({s["shot"] for s in rep["shots"] if any(not s["gates"].get(g, True) for g in SHOT_GATES)})
        # typed diagnoses decide what is regenerated and how (a stale expectation or dead air is not a reason)
        rp = {k: v for k, v in repair_plan(run, rep, rnd).items() if k in flagged} if rnd < a.rounds else {}
        log["rounds"].append({"round": rnd, "passed": rep["passed"], "total": rep["total"], "flagged_shots": flagged,
                              "repairs": {k: {"types": v["types"], "attempt": v["attempt"]} for k, v in rp.items()},
                              "film_gates": rep["film_gates"]})
        print(f"[produce] round {rnd}: {rep['passed']}/{rep['total']} gates, flagged: {flagged}, "
              f"repairing: { {k: v['types'] for k, v in rp.items()} }", flush=True)
        assets_p = run / "memory" / f"assets_round_{rnd}.json"
        if rnd < a.rounds and assets_p.exists():   # asset-level repair first: re-make the sheet, re-shoot its shots
            remade = {}
            st_p = run / "memory" / "repair_state.json"
            for cid, note in json.loads(assets_p.read_text()).items():
                try:
                    sh(PY, "tools/remake_asset.py", run, "--char", cid, "--note",
                       f"QA found: {note}. Follow the written age, gender and outfit exactly.")
                    remade[cid] = note
                    st = json.loads(st_p.read_text()); st.setdefault("__remade__", []).append(cid)
                    st_p.write_text(json.dumps(st, ensure_ascii=False, indent=1))
                except subprocess.CalledProcessError:
                    print(f"[produce] could not remake {cid}; continuing with shot-level repairs", flush=True)
            names = {c["id"]: c["name"] for c in json.loads((run / "assets" / "asset_library.json").read_text())["characters"]}
            for sq in rep["shots"]:
                if any(names.get(c) in (sq.get("characters") or []) for c in remade) and sq["shot"] not in rp:
                    rp[sq["shot"]] = {"prefix": "", "suffix": "", "seed_offset": 0, "duration_delta": 0.0,
                                      "judge_prompt": None, "types": ["asset"], "attempt": 0}
            log["rounds"][-1]["remade_assets"] = remade
            log["rounds"][-1]["repairs"] = {k: {"types": v["types"], "attempt": v["attempt"]} for k, v in rp.items()}
            print(f"[produce] remade assets {list(remade)}; re-shooting {sorted(rp)}", flush=True)
        if not rp:
            break
        (run / "memory" / f"repair_round_{rnd}.json").write_text(json.dumps(rp, ensure_ascii=False, indent=1))
        sh(PY, "tools/resume_production.py", run, "--only", ",".join(rp), "--resync-characters", "--max-retries", "1",
           "--repair", run / "memory" / f"repair_round_{rnd}.json")
    # final tier: re-render the closing shot and the shots still failing after the repair rounds on the full-schedule
    # H3 replicas (no turbo LoRA), when they are configured (H3_FINAL_*_URL)
    if os.environ.get("H3_FINAL_FL2VA_URL") or os.environ.get("H3_FINAL_REF2VA_URL") or _dotenv_has("H3_FINAL_"):
        # bounded: a full-schedule clip costs ~6x a draft one and each tier has one replica per mode, so the closing
        # shot goes first, then the shortest still-failing shots, at most --final-max in all
        shots = [s["shot"] for s in rep["shots"]]
        dur = {s["shot"]: float(s.get("duration") or 99) for s in rep["shots"]}
        keep_failing = [s["shot"] for s in rep["shots"] if any(not s["gates"].get(g, True) for g in SHOT_GATES)]
        rest = sorted((x for x in keep_failing if x not in shots[-1:]), key=lambda x: dur.get(x, 99))
        final = sorted((shots[-1:] + rest)[:a.final_max])
        log["final_tier"] = final
        print(f"[produce] final tier (full-schedule H3) for {final}", flush=True)
        sh(PY, "tools/resume_production.py", run, "--only", ",".join(final), "--resync-characters", "--max-retries", "0",
           "--tier", "final")
    sh("python3", "tools/post_production.py", run)
    final = qa(run, a.hint, post=True)
    log.update(final={"passed": final["passed"], "total": final["total"], "all_pass": final["all_pass"],
                      "film_gates": final["film_gates"], "film_length": final["film_length"]},
               wall_s=round(time.time() - t0))
    (run / "produce_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1))
    print(f"[produce] final: {final['passed']}/{final['total']} gates, all_pass={final['all_pass']}, "
          f"{log['wall_s']} s -> {run / 'media' / 'film_post.mp4'}", flush=True)


if __name__ == "__main__":
    main()
