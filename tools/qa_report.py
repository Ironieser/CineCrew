#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
qa_report: automatic quality gates for a rendered run (audio, visuals, pacing). Writes <run>/qa_report.json and .md.

  python tools/qa_report.py <run_dir> [--hint "domain words"] [--no-vlm] [--film <mp4>]

Gates (per shot unless noted) — hard gates, chosen on the calibration set (data/calib, precision 0.80 / recall 0.57
for the visual ones vs 0.43 / 0.43 for the previous judge + VLM set):
  audio.asr          dialogue line recognised (faster-whisper, char similarity >= 0.85; short lines: one char off)
  audio.dead_air     dialogue shots: speech starts <= 1.5 s and ends >= duration - 2.0 s (post-production trims it)
  visual.continuity  time of day / rain read from frames match the continuity ledger (night is strict)
  visual.text        no prominent garbled text (VLM transcription; adjacent repeated tokens count as garbled)
  visual.identity    expected characters match their reference board; no glowing human eyes
  visual.presence    no stranger; with a closed cast (a "no people other than ..." world fact) the humans on screen are
                     counted (count_humans.yaml) and may not outnumber the cast's people (robots / animals excluded)
  audio.voice        same speaker across shots: speaker-embedding cosine >= 0.75 (resemblyzer)   [film-level]
  audio.loudness     dialogue clips within 4 LU (EBU R128), ambience-only clips not louder        [film-level]
  content.dialogue_coverage  every quoted script line is spoken                                  [film-level]
  content.no_repeated_lines  no line is spoken more often than the script has it                 [film-level]
  pacing.length      film length within ±25 % of the planned total                                  [film-level]
Advisory (recorded under "advisory", never gate): visual.review (VisualJudge score), visual.vlm (presence count,
generic flags).
Needs: ffmpeg, faster-whisper, resemblyzer (local python), LLM_* (VLM) from .env.
"""

import argparse
import base64
import difflib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CN = {"零": "0", "一": "1", "二": "2", "两": "2", "三": "3", "四": "4", "五": "5", "六": "6", "七": "7", "八": "8", "九": "9"}


def norm(s):
    s = re.sub(r"[\s，。？！、,.?!;；:：“”\"'（）()—\-…]", "", s or "")
    return "".join(CN.get(c, c) for c in s)


def duration(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout.strip() or 0)


def mean_volume(p):
    # EBU R128 integrated loudness (LUFS): gated, so pauses do not drag the value down like a plain mean would
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(p), "-af", "ebur128", "-vn", "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None


def frames(p, n=3):
    d = duration(p); out = []
    tmp = Path(tempfile.mkdtemp())
    for k in range(n):
        f = tmp / f"f{k}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{d * (k + 1) / (n + 1):.2f}", "-i", str(p), "-frames:v", "1",
                        "-vf", "scale=1344:-2", str(f)], check=True)
        out.append(f)
    return out


VLM_PROMPT = """You check frames from one shot of a film. Expected characters on screen: {chars}.
The film's whole cast (any of them may also appear at the edge or in the background): {cast}.
Answer ONLY JSON: {{"garbled_text": bool, "captions_or_subtitles": bool, "human_glowing_eyes": bool,
"figures_visible": int, "visible_text": [{{"text": "...", "garbled": bool, "prominent": bool}}],
"identity_mismatch": ["names of expected characters who do NOT look like their reference image"],
"expected_characters_present": bool, "wrong_extra_person": bool, "duplicated_unique_object": bool, "time_of_day": "day|dusk|night|unclear", "raining": "yes|no|unclear",

"notes": "short"}}
- garbled_text: any malformed/fake lettering visible (signs, labels, screens). Ignore abstract waveforms and icons.
- human_glowing_eyes: a human's eyes emit light (not just reflections).
- visible_text: transcribe ALL text-like marks in the CLIP frames only (never the reference board): signs, shop fronts,
  route boards, LED displays, labels, posters, badges, screens. Copy what you see even if garbled. For each item:
  garbled = malformed characters, nonsense or repeated / broken words (a real word or a plain number is not garbled);
  prominent = large or central enough that a viewer would read it (a small badge number or a tiny label is not).
  At most 12 items (the most prominent first). [] only if there is none.
- identity_mismatch: compare each expected character with the reference board (last image, if given): a different
  species or breed, age group, gender, face or outfit is a mismatch. Do not count pose, lighting or framing.
- figures_visible: how many distinct people or robots are visible in any frame; silhouettes, back views and
  out-of-focus foreground figures count.
- expected_characters_present: for each expected character a figure consistent with them is visible, robots
  included. A back view, an over-the-shoulder foreground or a silhouette counts as present: you are not asked to
  confirm identity, only that nobody expected is missing.
- wrong_extra_person: a clearly visible person who matches NONE of the film's cast (a stranger), or a cast member
  shown twice. A cast member at the edge or in the background is fine. Each cast member is at most ONE person in a
  frame: if more people are visible than cast members they could be (two older women when the cast has one), the
  extra ones are strangers. Never excuse a person as "probably part of the cast" without naming who they are.
- time_of_day: judge from the sky, windows and light (an interior with black windows and lamps on is night).
- raining: rain drops, wet streaks on windows, wet reflective streets, umbrellas in use.
- duplicated_unique_object: a one-of-a-kind object appears twice in one frame (two Earths, two suns, two moons, the same person twice)."""


def reference_board(refs):
    """One labelled board of the expected characters' reference sheets (sent after the clip frames)."""
    from PIL import Image, ImageDraw
    tiles = [(n, Image.open(p).convert("RGB")) for n, p in refs if Path(p).exists()]
    if not tiles:
        return None
    h = 300; tiles = [(n, t.resize((int(t.width * h / t.height), h))) for n, t in tiles]
    W = sum(t.width for _, t in tiles) + 20 * (len(tiles) + 1); board = Image.new("RGB", (W, h + 90), (30, 30, 30))
    d = ImageDraw.Draw(board); d.text((20, 12), "REFERENCE IMAGES - NOT PART OF THE CLIP", fill=(255, 220, 0)); x = 20
    for n, t in tiles:
        board.paste(t, (x, 50)); d.text((x, h + 60), n, fill=(255, 255, 255)); x += t.width + 20
    out = Path(tempfile.mkdtemp()) / "refs.jpg"; board.save(out, quality=88)
    return out


def world_checks(frame, facts, cast="", action=""):
    """Describe the frame blind, then judge the world facts from the text (a VLM primed with the facts reports what
    it was told to look for). Same agents as the keyframe FrameCheck."""
    from src.engine import ConfigurableAgent
    from src.agents.dailies_reviewer.frame_check import BUILTIN_FACTS
    d = ROOT / "src" / "agents" / "dailies_reviewer"
    desc = ConfigurableAgent(config_path=str(d / "frame_describe.yaml")).run(images=[str(frame)])
    allf = BUILTIN_FACTS + list(facts)
    wv = ConfigurableAgent(config_path=str(d / "world_judge.yaml")).run(cast=cast or "unknown", action=action or "-",
        facts=" ".join(f"({i}) {f}" for i, f in enumerate(allf, 1)), description=desc.model_dump_json())
    out = []
    for c in wv.checks:   # re-index onto the story's own facts (built-ins first)
        c = dict(c); i = int(c.get("fact") or 0)
        c["fact"] = i - len(BUILTIN_FACTS) if i > len(BUILTIN_FACTS) else i
        c["text"] = allf[i - 1] if 1 <= i <= len(allf) else "?"
        out.append(c)
    out.append({"action_shown": wv.action_shown, "action_reason": wv.action_reason})
    return out


def vlm_check(paths, chars, cast="", board=None, facts=""):
    from openai import OpenAI
    from src.config import Config
    content = [{"type": "text", "text": VLM_PROMPT.format(chars=chars or "none (environment shot)", cast=cast or "unknown", facts=facts or "none given")}]
    for p in list(paths) + ([board] if board else []):
        content.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(Path(p).read_bytes()).decode()}})
    client = OpenAI(api_key=Config.LLM_API_KEY or "EMPTY", base_url=Config.LLM_BASE_URL)
    err = None
    for attempt in range(3):   # a long text list can still yield invalid JSON (unescaped quotes): retry
        r = client.chat.completions.create(model=Config.MODEL_NAME, temperature=0 if attempt == 0 else 0.2,
                                           max_tokens=1200, response_format={"type": "json_object"},
                                           messages=[{"role": "user", "content": content}])
        try:
            return json.loads(r.choices[0].message.content)
        except json.JSONDecodeError as e:
            err = e
    raise err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir"); ap.add_argument("--hint", default=""); ap.add_argument("--no-vlm", action="store_true")
    ap.add_argument("--film", default=None)
    ap.add_argument("--post", action="store_true", help="grade the post_production output (scene_blueprint_post.json, film_post.mp4)")
    a = ap.parse_args()
    run = Path(a.run_dir)
    bp = json.loads((run / "shots" / ("scene_blueprint_post.json" if a.post else "scene_blueprint_final.json")).read_text())
    if a.post and not a.film:
        a.film = str(run / "media" / "film_post.mp4")
    raw_clip = {}
    ledger = {x["shot_id"]: x["narrative_layer"].get("continuity") for x in
              json.loads((run / "shots" / "scene_blueprint_final.json").read_text())["shots"]}
    if a.post:   # visual checks run on the pre-post clip: the burned-in subtitles are ours, not a model defect
        for s0 in json.loads((run / "shots" / "scene_blueprint_final.json").read_text())["shots"]:
            p0 = (((s0.get("render_layer") or {}).get("video") or {}).get("video_clip_paths") or [None])[0]
            if p0:
                raw_clip[s0["shot_id"]] = Path(p0) if Path(p0).is_absolute() else ROOT / p0
    lib = json.loads((run / "assets" / "asset_library.json").read_text())
    names = {c["id"]: c["name"] for c in lib.get("characters", [])}
    # expected on-screen characters from the current visible-character guard over the plan (same as the repair policy)
    expected = {}
    from src.agents.script_supervisor import judged_facts
    from src.agents.dailies_reviewer.frame_check import closed_cast, count_humans, human_cast
    from src.schemas.assets import AssetLibrary as _Lib
    people = human_cast(_Lib.model_validate(lib))   # cast members who are people (robots / animals are not)
    try:
        from src.schemas.blueprint import SceneBlueprint
        from src.schemas.assets import AssetLibrary
        from src.agents.technical_director.technical_director_agent import visible_characters
        alib = AssetLibrary.model_validate(lib)
        for ps in SceneBlueprint.model_validate_json((run / "shots" / "scene_blueprint_render_filled.json").read_text()).shots:
            if ps.render_layer:
                expected[ps.shot_id] = visible_characters(ps.render_layer.image.characters_in_shot, ps, alib)
    except Exception as e:
        print(f"[qa] expected characters from the final blueprint ({e})", flush=True)
    looks = {c["name"]: (c.get("description") or "")[:140] for c in lib.get("characters", [])}
    sheet_of = {c["name"]: ((c.get("visual_references") or {}).get("canonical_image_path")) for c in lib.get("characters", [])}
    from faster_whisper import WhisperModel
    from resemblyzer import VoiceEncoder, preprocess_wav
    import numpy as np
    asr = WhisperModel("small", device="cpu", compute_type="int8"); enc = VoiceEncoder("cpu")
    init = "以下是普通话的句子" + (f"，内容涉及{a.hint}。" if a.hint else "。")
    shots, voices, vols, planned = [], {}, [], 0.0
    for s in bp["shots"]:
        rl = s.get("render_layer") or {}; v = rl.get("video") or {}
        clip = (v.get("video_clip_paths") or [None])[0]
        planned += (s.get("staging_layer") or {}).get("duration_seconds") or 0
        if not clip or not (ROOT / clip).exists() and not Path(clip).exists():
            shots.append({"shot": s["shot_id"], "error": "no clip"}); continue
        clip = Path(clip) if Path(clip).exists() else ROOT / clip
        d = duration(clip); dia = (s["narrative_layer"].get("dialogue") or {})
        line = dia.get("text") if dia.get("has_dialogue") else None
        spk = names.get(dia.get("speaker_asset_id"), dia.get("speaker_asset_id"))
        chars = [names.get(c, c) for c in (expected.get(s["shot_id"]) if s["shot_id"] in expected
                                           else ((rl.get("image") or {}).get("characters_in_shot") or []))]
        r = {"shot": s["shot_id"], "clip": str(clip.relative_to(ROOT)) if str(clip).startswith(str(ROOT)) else str(clip),
             "duration": round(d, 2), "dialogue": line, "speaker": spk, "characters": chars, "gates": {},
             "advisory": {}}
        segs, _ = asr.transcribe(str(clip), language="zh", vad_filter=True, initial_prompt=init, word_timestamps=False)
        segs = list(segs); got = "".join(x.text for x in segs).strip()
        if line:
            sim = difflib.SequenceMatcher(None, norm(got), norm(line)).ratio()
            extra = len(norm(got)) - len(norm(line))
            dist = len(norm(line)) * (1 - sim) if len(norm(line)) <= 6 else 99   # short lines: one char ~ 0.2 similarity
            r["asr"] = got; r["gates"]["audio.asr"] = bool((sim >= 0.85 or dist <= 1.01) and extra <= 4)
            if segs:
                lead, tail = segs[0].start, d - segs[-1].end
                r["speech_span"] = [round(lead, 2), round(tail, 2)]
                r["gates"]["audio.dead_air"] = bool(lead <= 1.5 and tail <= 2.0)
                wav = Path(tempfile.mkdtemp()) / "a.wav"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-ss", f"{segs[0].start:.2f}", "-to", f"{segs[-1].end:.2f}",
                                "-ac", "1", "-ar", "16000", str(wav)], check=True)
                pw = preprocess_wav(str(wav))
                if len(pw) / 16000 >= 1.5:   # speaker embeddings of sub-1.5 s speech are too noisy to grade
                    voices.setdefault(spk or "unknown", []).append((s["shot_id"], enc.embed_utterance(pw)))
                else:
                    r["voice_skipped"] = f"speech {len(pw) / 16000:.2f}s < 1.5s"
            else:
                r["gates"]["audio.asr"] = False
        elif got and len(norm(got)) > 6:
            r["asr_unexpected_speech"] = got
        mv = mean_volume(clip); vols.append((mv, bool(line))); r["loudness_lufs"] = mv
        from src.skills.cut_detect import cuts as _cuts   # an internal hard cut = two shots rendered as one clip
        ct, _ = _cuts(str(raw_clip.get(s["shot_id"], clip)) if a.post else str(clip))
        if a.post:   # post-production trims edge cuts away; grade what is left in the post clip
            ct, _ = _cuts(str(clip))
        r["gates"]["visual.cut"] = not ct
        if ct:
            r["internal_cuts_s"] = [round(t, 2) for t in ct]
        att = (rl.get("visual_review") or {}).get("clips") or []
        scored = [x for c in att for x in c.get("attempts", []) if "score" in x]
        # the verdict on the clip actually kept (falls back to the latest one)
        src = raw_clip.get(s["shot_id"], clip)
        kept = [x for x in scored if x.get("video_path") and Path(x["video_path"]).name == Path(src).name
                and Path(x["video_path"]).parent.name == Path(src).parent.name] or scored[-1:]
        if kept:
            # advisory only: on the calibration set the judge verdict added false positives, not recall
            r["review_score"] = kept[-1]["score"]; r["advisory"]["visual.review"] = bool(kept[-1]["score"] >= 0.85)
        if not a.no_vlm:
            try:
                refs = [(c, sheet_of[c] if Path(sheet_of[c]).is_absolute() else str(ROOT / sheet_of[c]))
                        for c in chars if sheet_of.get(c)]
                frames_used = frames(raw_clip.get(s["shot_id"], clip))
                vj = vlm_check(frames_used,
                               "; ".join(f"{c} ({looks.get(c, '')})" for c in chars),
                               "; ".join(f"{n} ({looks.get(n, '')[:80]})" for n in names.values()),
                               reference_board(refs) if refs else None,
                               " ".join(f"({i}) {f}" for i, f in enumerate((ledger.get(s["shot_id"]) or {}).get("world_facts") or [], 1))); r["vlm"] = vj
                items = [t if isinstance(t, dict) else {"text": str(t), "garbled": True, "prominent": True}
                         for t in (vj.get("visible_text") or [])]
                r["visible_text"] = items
                # calibrated: plausible small text (badge numbers, safety labels) is fine; garbled AND prominent fails
                def broken(t):   # deterministic: an adjacent repeated token ("2路 路") is generator garbage
                    toks = re.findall(r"[\u4e00-\u9fff]|[A-Za-z]+|\d+", str(t))
                    return any(a == b and not a.isdigit() for a, b in zip(toks, toks[1:]))
                bad = [t["text"] for t in items if t.get("prominent") and (t.get("garbled") or broken(t.get("text")))
                       and "REFERENCE" not in str(t.get("text", "")).upper()]
                r["gates"]["visual.text"] = not bad
                if bad:
                    r["bad_text"] = bad
                mism = [m for m in (vj.get("identity_mismatch") or []) if m]
                if chars:
                    if vj.get("human_glowing_eyes"):
                        mism = mism + ["glowing human eyes"]
                    r["gates"]["visual.identity"] = not mism
                    if mism:
                        r["identity_mismatch"] = mism
                facts = judged_facts((ledger.get(s["shot_id"]) or {}).get("world_facts"))   # presence: own gate
                wv = []
                wc = world_checks(frames_used[len(frames_used) // 2], facts,
                                  "; ".join(f"{n}: {looks.get(n, '')[:100]}" for n in names.values()),
                                  s["narrative_layer"].get("narrative_action", ""))
                act = wc.pop() if wc and "action_shown" in wc[-1] else {}
                if str(act.get("action_shown", "yes")).lower() == "no":   # the shot's main subject is missing
                    r["gates"]["visual.action"] = False
                    r["action_reason"] = act.get("action_reason", "")
                else:
                    r["gates"]["visual.action"] = True
                for c in wc:
                    if isinstance(c, dict) and str(c.get("verdict", "")).lower() == "violated" and c.get("evidence"):
                        wv.append(f"{c.get('text', '?')} — seen: {c.get('evidence')}")
                if True:   # built-in facts (one-of-a-kind bodies appear once) apply to every shot
                    r["gates"]["visual.world"] = not wv
                    if wv:
                        r["world_violations"] = wv
                # strangers (people outside the cast) are a hard failure; presence counts stay advisory
                r["gates"]["visual.presence"] = not vj.get("wrong_extra_person")
                if closed_cast((ledger.get(s["shot_id"]) or {}).get("world_facts")):
                    # counted, not asked: a VLM asked "is there a stranger?" misses small background people
                    n_h = max(len(count_humans(str(f))) for f in frames_used[:2])
                    r["humans_counted"] = n_h
                    if n_h > len(people):
                        r["gates"]["visual.presence"] = False
                        r["strangers"] = f"{n_h} people on screen, the cast has {len(people)}"
                r["advisory"]["visual.vlm"] = bool(not vj.get("garbled_text") and not vj.get("captions_or_subtitles")
                                                and not vj.get("human_glowing_eyes")
                                                and (not chars or vj.get("expected_characters_present", True)
                                                     or int(vj.get("figures_visible") or 0) >= len(chars))
                                                and not vj.get("wrong_extra_person") and not vj.get("duplicated_unique_object"))
            except Exception as e:
                r["vlm_error"] = str(e)
        cont = ledger.get(s["shot_id"]) or {}
        if cont and r.get("vlm"):   # continuity ledger vs what the frames show (coarse cues only: VLMs read them reliably)
            vj = r["vlm"]; seen = str(vj.get("time_of_day", "unclear")).lower()
            want = cont.get("time_of_day")
            # night is strict: overcast daylight is what generators drift to, and the VLM calls it "dusk"
            dark = {"night": {"night"}, "dusk": {"dusk", "night", "day"}, "dawn": {"dawn", "day", "dusk"},
                    "day": {"day", "dusk", "dawn"}}
            ok_t = want == "none" or seen == "unclear" or seen in dark.get(want, {seen})
            rain_wanted = "rain" in (cont.get("weather") or "").lower()
            ok_w = not rain_wanted or str(vj.get("raining", "unclear")).lower() != "no"
            r["continuity_expected"] = {"time_of_day": want, "weather": cont.get("weather")}
            r["gates"]["visual.continuity"] = bool(ok_t and ok_w)
        shots.append(r); print(f"[qa] {s['shot_id']}: {r['gates']}", flush=True)

    film_gates = {}
    vsim = {}
    for spk, embs in voices.items():
        if len(embs) > 1:
            E = np.stack([e for _, e in embs]); C = E @ E.T
            m = float(np.min(C[np.triu_indices(len(embs), 1)])); vsim[spk] = round(m, 3)
            film_gates[f"audio.voice[{spk}]"] = bool(m >= 0.75)
    dv = [x for x, d in vols if x is not None and d]; av = [x for x, d in vols if x is not None and not d]
    vv = dv + av
    if dv:   # dialogue level consistent across shots; ambience-only shots never louder than speech
        film_gates["audio.loudness"] = bool(max(dv) - min(dv) <= 4 and (not av or max(av) <= min(dv)))
    if (run / "script.txt").exists():   # content: every quoted script line is spoken in the film's plan
        from collections import Counter
        from src.skills.script_coverage import missing_lines, norm as cnorm, script_lines
        script = (run / "script.txt").read_text()
        miss = missing_lines(script, [x.get("dialogue") or "" for x in shots])
        film_gates["content.dialogue_coverage"] = not miss
        # a line said more often than the script has it (a recovered line re-assigned to a second shot)
        have, said = Counter(cnorm(l) for l in script_lines(script)), Counter(cnorm(x["dialogue"]) for x in shots if x.get("dialogue"))
        repeated = [x["dialogue"] for x in shots if x.get("dialogue") and have.get(cnorm(x["dialogue"]))
                    and said[cnorm(x["dialogue"])] > have[cnorm(x["dialogue"])]]
        film_gates["content.no_repeated_lines"] = not repeated
        content = {"script_lines": len(script_lines(script)), "missing_lines": miss, "repeated_lines": sorted(set(repeated))}
    else:
        content = None
    # pacing metrics (advisory until calibrated on our own films): shot lengths, time to the first line, the longest
    # stretch without speech
    durs = [x.get("duration", 0) for x in shots if x.get("duration")]
    t, first_line, gaps, last_speech = 0.0, None, [], 0.0
    for x in shots:
        if x.get("dialogue") and x.get("speech_span"):
            lead, tail = x["speech_span"]
            if first_line is None:
                first_line = round(t + lead, 2)
            gaps.append(t + lead - last_speech); last_speech = t + x["duration"] - tail
        t += x.get("duration", 0)
    gaps.append(t - last_speech)
    pacing = {"shots": len(durs), "avg_shot_s": round(sum(durs) / len(durs), 2) if durs else None,
              "max_shot_s": max(durs) if durs else None, "first_line_s": first_line,
              "longest_silence_s": round(max(gaps), 2) if gaps else None}
    film = Path(a.film) if a.film else run / "media" / "film.mp4"
    flen = duration(film) if film.exists() else sum(x.get("duration", 0) for x in shots)
    film_gates["pacing.length"] = bool(abs(flen - planned) <= 0.25 * planned) if planned else True
    total = [g for x in shots for g in x.get("gates", {}).values()] + list(film_gates.values())
    report = {"run": str(run), "film": str(film), "film_length": round(flen, 2), "planned_length": round(planned, 2),
              "voice_min_similarity": vsim, "content": content, "pacing": pacing, "loudness_range_db": [min(vv), max(vv)] if vv else None,
              "film_gates": film_gates, "shots": shots,
              "vlm_errors": sum(1 for x in shots if x.get("vlm_error")), "passed": sum(total), "total": len(total), "all_pass": all(total)}
    out = run / ("qa_report_post" if a.post else "qa_report")
    out.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    md = [f"# QA report — {run.name}", f"film {flen:.1f}s (planned {planned:.1f}s) · gates {sum(total)}/{len(total)} · "
          f"{'ALL PASS' if all(total) else 'FAIL'}", "", "| shot | dur | review | gates failed | notes |", "|---|---|---|---|---|"]
    for x in shots:
        bad = [k for k, v in x.get("gates", {}).items() if not v]
        note = (x.get("vlm") or {}).get("notes", "") if bad else ""
        md.append(f"| {x['shot']} | {x.get('duration', '')} | {x.get('review_score', '')} | {', '.join(bad) or '—'} | {note} |")
    md += ["", f"film gates: {film_gates}", f"voice min cosine per speaker: {vsim}", f"pacing: {pacing}"]
    out.with_suffix(".md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
