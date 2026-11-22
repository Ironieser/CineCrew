#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Repair policy: QA failures -> typed diagnoses -> per-shot repair plan (prompt additions, seed, duration), plus a
story-level lesson memory. Templates live in configs/repair_policy.yaml; this module only routes.

  diagnose(shot_qa, review_attempt, ledger)      -> [(type, evidence)]
  plan(run_dir, qa_report, round_no)             -> {shot_id: {"prefix", "suffix", "seed_offset", "duration_delta",
                                                     "judge_prompt", "types", "attempt"}}  (+ updates memory files)
Memory files under <run>/memory/: repair_state.json (attempts and diagnoses per shot), lessons.json (story level).
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = yaml.safe_load((ROOT / "configs" / "repair_policy.yaml").read_text())


def _review_of_kept(shot_bp: dict, clip: str) -> dict:
    att = [x for c in ((shot_bp.get("render_layer") or {}).get("visual_review") or {}).get("clips", [])
           for x in c.get("attempts", []) if "score" in x]
    tail = lambda x: Path(x).parts[-2:]
    kept = [x for x in att if x.get("video_path") and tail(x["video_path"]) == tail(clip)]
    return (kept or att[-1:] or [{}])[-1]


def diagnose(q: dict, review: dict, ledger: dict) -> List[Tuple[str, str]]:
    """Map one shot's QA record (+ the judge verdict of its kept clip) to typed failures with evidence text."""
    g, v, out = q.get("gates", {}), q.get("vlm") or {}, []
    chk = review.get("checks") or {}
    issues = "; ".join(review.get("issues") or [])[:300]
    if g.get("visual.identity") is False:
        out.append(("A", "does not look like the reference: " + ", ".join(q.get("identity_mismatch") or [])))
    elif v.get("human_glowing_eyes") or chk.get("identity_matches") is False:
        out.append(("A", "glowing human eyes" if v.get("human_glowing_eyes") else issues or "identity drift"))
    exp = len(q.get("characters") or [])
    if (g.get("visual.vlm") is False and (v.get("wrong_extra_person") or v.get("duplicated_unique_object")
                                          or (exp and int(v.get("figures_visible") or 0) < exp)))\
            or chk.get("right_characters") is False:
        out.append(("B", v.get("notes") or issues or "wrong characters on screen"))
    if g.get("visual.presence") is False:
        out.append(("B", "a person who is not in the cast appears: " + (v.get("notes") or "stranger in frame")))
    if g.get("visual.world") is False:
        out.append(("C", "the frames contradict the film's world: " + "; ".join(q.get("world_violations") or [])))
    if g.get("visual.action") is False:
        out.append(("E", "the shot's main subject is not shown: " + (q.get("action_reason") or "")))
    if g.get("visual.continuity") is False:
        ce = q.get("continuity_expected") or {}
        out.append(("C", f"the frames read as {v.get('time_of_day')} (raining: {v.get('raining')}) but the shot is "
                         f"{ce.get('time_of_day')}, {ce.get('weather')}"))
    if g.get("visual.text") is False:
        out.append(("D", "garbled text visible: " + "; ".join(str(t) for t in (q.get("bad_text") or [])[:4])))
    elif v.get("garbled_text") or v.get("captions_or_subtitles") or chk.get("integrity_ok") is False:
        out.append(("D", "generated text / signage visible" if (v.get("garbled_text") or v.get("captions_or_subtitles"))
                    else issues or "visual artifact"))
    if g.get("visual.review") is False and (chk.get("main_action_shown") is False or not chk) and \
            not any(t in ("A", "B", "D") for t, _ in out):
        out.append(("E", issues or "main action not shown"))
    if chk.get("constraints_ok") is False and issues and not any(t in ("C", "D") for t, _ in out):
        low = issues.lower()
        if any(w in low for w in ("text", "sign", "letter", "logo", "label", "caption", "display", "extra", "two ",
                                  "duplicate")):
            out.append(("D", issues))
        elif ledger and any(w in low for w in ("night", "day", "dusk", "dawn", "rain", "weather", "light", "holds",
                                               "holding", "umbrella", "wear")):
            out.append(("C", issues))
        else:
            out.append(("E", issues))
    if g.get("audio.asr") is False:   # dead air alone is trimmed in post, not regenerated
        out.append(("F", f"heard \"{q.get('asr', '')}\" for the line \"{q.get('dialogue', '')}\"; speech span (lead, tail) "
                         f"= {q.get('speech_span')}"))
    failing = [k for k, val in g.items() if val is False and k != "audio.dead_air"]
    vlm_flags = any(v.get(k) for k in ("garbled_text", "captions_or_subtitles", "human_glowing_eyes",
                                       "wrong_extra_person", "duplicated_unique_object"))
    if not out and failing and not (failing == ["visual.vlm"] and not vlm_flags):
        out.append(("E", issues or "failed QA"))
    return out


def _clean(ev: str) -> str:
    return (ev or "").strip().rstrip(".。;； ")


def _fmt(t: str, **kw) -> str:
    class D(dict):
        def __missing__(self, k):
            return ""
    return t.format_map(D(**kw)).strip()


def plan(run: Path, qa: dict, round_no: int) -> Dict[str, dict]:
    run = Path(run); mem = run / "memory"; mem.mkdir(exist_ok=True)
    state_p, lessons_p = mem / "repair_state.json", mem / "lessons.json"
    state = json.loads(state_p.read_text()) if state_p.exists() else {}
    lessons = json.loads(lessons_p.read_text()) if lessons_p.exists() else {}
    bp = {s["shot_id"]: s for s in json.loads((run / "shots" / "scene_blueprint_final.json").read_text())["shots"]}
    from src.agents.technical_director.technical_director_agent import visible_characters
    from src.schemas.blueprint import SceneBlueprint
    planned = {s.shot_id: s for s in SceneBlueprint.model_validate_json(
        (run / "shots" / "scene_blueprint_render_filled.json").read_text()).shots}
    lib = json.loads((run / "assets" / "asset_library.json").read_text())
    names = {c["id"]: c["name"] for c in lib.get("characters", [])}
    from src.agents.script_supervisor.script_supervisor_agent import continuity_sentence
    from src.schemas.assets import AssetLibrary
    from src.schemas.blueprint import ContinuityState
    alib = AssetLibrary.model_validate(lib)

    out, seen_types, asset_evidence = {}, {}, {}
    # only identity attributes justify re-making a sheet; states (a screen's content, expression, pose, held props,
    # lights) change from shot to shot and are fixed per shot
    SPEC = ("age", "toddler", "child", "older", "younger", "gender", "too young", "too old", "species", "breed",
            "a boy", "a girl", "a man", "a woman", "elderly", "teenager", "years old")
    STATE = ("screen", "display", "waveform", "expression", "pose", "holding", "light", "smil", "eyes closed",
             "posture", "facing", "position")
    for q in qa["shots"]:
        sid = q["shot"]
        if not any(v is False for k, v in q.get("gates", {}).items() if k != "audio.dead_air"):
            continue
        shot = bp.get(sid) or {}
        ledger = (shot.get("narrative_layer") or {}).get("continuity")
        review = _review_of_kept(shot, q.get("clip", ""))
        ps = planned.get(sid)
        on_screen = (visible_characters(ps.render_layer.image.characters_in_shot, ps, alib)
                     if ps is not None and ps.render_layer else
                     (shot.get("render_layer") or {}).get("image", {}).get("characters_in_shot") or [])
        q = dict(q, characters=[names.get(c, c) for c in on_screen])   # expectation from the current guard
        diags = diagnose(q, review, ledger)
        if not diags:   # it only failed against a stale expectation: nothing to regenerate
            continue
        st = state.setdefault(sid, {"attempt": 0, "history": []})
        st["attempt"] += 1
        st["history"].append({"round": round_no, "diagnoses": diags})
        k = min(st["attempt"], 2) - 1                                   # templates for attempt 1 / 2+
        cont = continuity_sentence(ContinuityState.model_validate(ledger), alib, set(on_screen)) if ledger else ""
        kw = dict(n_expected=len(on_screen), expected=", ".join(names.get(c, c) for c in on_screen) or "none",
                  continuity=cont, action=(shot.get("narrative_layer") or {}).get("narrative_action", ""))
        pre, suf, dd, judge_prompt = [], [], 0.0, None
        for t, ev in diags:
            seen_types.setdefault(t, set()).add(sid)
            if t == "A":   # identity contradicts the written character: attribute per sentence, not per paragraph
                import re as _re
                for sent in _re.split(r"[;；]|(?<=[.。])\s", ev):
                    low = sent.lower()
                    if not any(w in low for w in SPEC) or any(w in low for w in STATE):
                        continue
                    first = lambda c: names.get(c, "").lower().split(" (")[0]
                    hit = sorted([c for c in on_screen if first(c) and first(c) in low], key=lambda c: low.index(first(c)))
                    hit = hit[:1] or (on_screen if len(on_screen) == 1 else [])
                    for c in hit:
                        asset_evidence.setdefault(c, {})[sid] = sent.strip()
            tmpl = POLICY["types"][t][k]
            if tmpl.get("prefix"):
                pre.append(_fmt(tmpl["prefix"], evidence=_clean(ev), **kw))
            if tmpl.get("suffix"):
                suf.append(_fmt(tmpl["suffix"], evidence=_clean(ev), **kw))
            dd += float(tmpl.get("duration_delta", 0))
            if tmpl.get("use_judge_prompt") and review.get("revised_prompt"):
                judge_prompt = review["revised_prompt"]
        if any(t == "F" for t, _ in diags) and q.get("gates", {}).get("audio.dead_air") is False and \
                (q.get("speech_span") or [0, 0])[1] > 2.0:
            dd = -1.0                                                    # too much tail: shorter clip, not longer
        out[sid] = {"prefix": " ".join(x for x in pre if x), "suffix": " ".join(x for x in suf if x),
                    "seed_offset": POLICY["seed_step"] * st["attempt"], "duration_delta": dd,
                    "judge_prompt": judge_prompt, "types": [t for t, _ in diags], "attempt": st["attempt"]}

    # story-level lessons: a type seen in >= lesson_min_shots shots this round
    glob = ""
    first = next((s for s in bp.values() if (s.get("narrative_layer") or {}).get("continuity")), None)
    if first:
        c = first["narrative_layer"]["continuity"]
        glob = f"The whole film is {c.get('time_of_day')}, {c.get('weather')}."
    for t, shots in seen_types.items():
        txt = _fmt(POLICY["lesson_text"].get(t, ""), continuity_global=glob)
        if txt and len(shots) >= POLICY["lesson_min_shots"]:
            lessons[t] = {"text": txt, "shots": sorted(shots), "round": round_no}
    lesson_txt = " ".join(v["text"] for v in lessons.values())
    for sid in out:
        if lesson_txt:
            out[sid]["suffix"] = (out[sid]["suffix"] + " Lessons from this film so far: " + lesson_txt).strip()
    # asset-level repair: the same character contradicts its description in >= lesson_min_shots shots -> the
    # reference sheet itself is wrong; re-making it beats asking every shot to copy it harder
    remake = {c: " | ".join(list(ev.values())[:2]) for c, ev in asset_evidence.items()
              if len(ev) >= POLICY["lesson_min_shots"] and c not in state.get("__remade__", [])}
    if remake:   # produce.py records "__remade__" only after the new sheet was actually rendered
        (mem / f"assets_round_{round_no}.json").write_text(json.dumps(remake, ensure_ascii=False, indent=1))
    state_p.write_text(json.dumps(state, ensure_ascii=False, indent=1))
    lessons_p.write_text(json.dumps(lessons, ensure_ascii=False, indent=1))
    (mem / f"repair_round_{round_no}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return out
