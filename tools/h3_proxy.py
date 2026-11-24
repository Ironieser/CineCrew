#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
h3_proxy: OpenAI-Videos-compatible front for a self-hosted MiniMax H3 (SGLang), so the pipeline's
VideoClient talks to H3 without model-specific code in src/ (see AGENTS.md: "run it behind an
OpenAI-compatible server").

    POST /v1/videos                 create  (JSON or multipart; VideoJob fields arrive via extra_body)
    GET  /v1/videos/{id}            poll    -> {"id", "status": queued|in_progress|completed|failed, "error"}
    GET  /v1/videos/{id}/content    mp4 bytes

Per request it
  1. collects prompt + extra fields (dialogue, voice_instructions, speaker, reference_subjects, duration, seed),
  2. copies reference images to a path the H3 server can read (REF_REMOTE_DIR, via scp to REF_SSH_HOST),
  3. rewrites the shot prompt into H3's structured format with an LLM (LLM_* env, e.g. the same
     OpenAI-compatible Qwen3-VL used by the pipeline) — dialogue as <d>[Chinese] ...</d>,
  4. validates the rewrite deterministically (exact dialogue, no <d> when silent, no-captions clause),
  5. submits to Ref2VA (when reference images exist) or FL2VA t2va, and maps status/content back.

Env:
  H3_FL2VA_URL   default http://127.0.0.1:30010/v1     H3_REF2VA_URL  default http://127.0.0.1:30020/v1
  H3_STEPS       default 8 (8-step LoRA)               H3_PROXY_PORT  default 30100
  REF_SSH_HOST   ssh alias that can write REF_REMOTE_DIR (shared FS visible to the H3 nodes)
  REF_REMOTE_DIR absolute dir on the cluster, e.g. /home/<user>/h3/refs
  LLM_BASE_URL / LLM_API_KEY / LLM_MODEL   prompt-rewrite model (OpenAI chat API)
  H3_DIALOGUE_LANG default Chinese
Run: python tools/h3_proxy.py   then set VIDEO_BASE_URL=http://127.0.0.1:30100/v1 VIDEO_MODEL=minimax-h3
"""

import email.parser
import email.policy
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config import Config  # noqa: E402  (loads .env)

# comma-separated URLs = replicas of the same variant; each request goes to the one with the fewest jobs in flight
FL2VA_URLS = [u.strip().rstrip("/") for u in os.getenv("H3_FL2VA_URL", "http://127.0.0.1:30010/v1").split(",") if u.strip()]
REF2VA_URLS = [u.strip().rstrip("/") for u in os.getenv("H3_REF2VA_URL", "http://127.0.0.1:30020/v1").split(",") if u.strip()]
FL2VA, REF2VA = FL2VA_URLS[0], REF2VA_URLS[0]
# final tier: replicas WITHOUT the 8-step turbo LoRA, run at the full schedule (key shots, still-failing shots)
FINAL_FL2VA_URLS = [u.strip().rstrip("/") for u in os.getenv("H3_FINAL_FL2VA_URL", "").split(",") if u.strip()]
FINAL_REF2VA_URLS = [u.strip().rstrip("/") for u in os.getenv("H3_FINAL_REF2VA_URL", "").split(",") if u.strip()]
FINAL_STEPS = int(os.getenv("H3_FINAL_STEPS", "50"))
INFLIGHT = {u: 0 for u in FL2VA_URLS + REF2VA_URLS + FINAL_FL2VA_URLS + FINAL_REF2VA_URLS}


_HEALTH = {}   # url -> (ok, checked_at)


def healthy(u: str) -> bool:
    ok, t = _HEALTH.get(u, (None, 0))
    if ok is None or time.time() - t > 60:
        try:
            ok = urllib.request.urlopen(u.rsplit("/v1", 1)[0] + "/health", timeout=5).status == 200
        except Exception:
            ok = False
        _HEALTH[u] = (ok, time.time())
    return ok


def pick(urls):
    """Replica with the fewest jobs in flight among the healthy ones (a replica whose allocation ended drops out)."""
    live = [u for u in urls if healthy(u)] or urls
    with _LOCK:
        u = min(live, key=lambda x: INFLIGHT.get(x, 0)); INFLIGHT[u] = INFLIGHT.get(u, 0) + 1
        return u


def release(u):
    with _LOCK:
        INFLIGHT[u] = max(0, INFLIGHT.get(u, 0) - 1)
STEPS = int(os.getenv("H3_STEPS", "8"))
# dialogue shots in two passes: FL2VA from the checked keyframe (silent, composition pinned), then Ref2VA video editing
# of that clip (<Video 1>) with the speaker's voice (<Audio 1>) to add the line. Ref2VA alone treats the keyframe as a
# loose reference and re-composes the shot (a planet seen whole became an orbital horizon).
TWO_PASS = os.getenv("H3_DIALOGUE_TWO_PASS", "0").lower() in ("1", "true", "yes")
SILENT_TAKE = "\nThe characters are silent in this take: mouths closed, no speech."
PORT = int(os.getenv("H3_PROXY_PORT", "30100"))
REF_SSH_HOST = os.getenv("REF_SSH_HOST", "")
REF_REMOTE_DIR = os.getenv("REF_REMOTE_DIR", "")
LANG = os.getenv("H3_DIALOGUE_LANG", "Chinese")
LOG_DIR = ROOT / "data" / "h3_proxy"
LOG_DIR.mkdir(parents=True, exist_ok=True)

JOBS = {}  # proxy id -> {"base": url, "h3_id": str, "status": ..., "error": ...}
_LOCK = threading.Lock()

REWRITE_SYSTEM = """You convert one film shot description into a MiniMax H3 video prompt. Output ONLY the prompt text.

Format (exact field names, this order, each followed by a newline):
{fmt}

Rules:
- Write everything in English except the spoken line, which stays verbatim in its original language.
- If "dialogue" is given, the output MUST contain its "required_markup" string exactly once, copied character for
  character, inside the [Shot 1] description at the moment the speaker talks.
- Spoken dialogue: give the speaker a stable ID (S1, S2...), describe the voice (age, gender, pitch, timbre, pace,
  emotion) OUTSIDE the tag, then put exactly the given line inside: <d>[{lang}] LINE</d>. Never translate, shorten or
  change the line. After the line, say the speaker closes their lips. Off-screen voices: "says in an off-screen
  voiceover:" and state the on-screen characters' lips stay closed.
- If no dialogue is given, nobody speaks: do not use <d> at all; describe only actions, ambience and sound.
- Describe composition, subjects, environment, action in playback order, camera movement, lighting.
- Always include the sentence "No subtitles, captions, or overlaid text appear on screen."
- Video models cannot render text: signs, shop fronts, route boards, displays and labels are out of focus, unlit or
  turned away, so no legible lettering appears anywhere in the frame.
- Human characters' eyes look natural and never glow; only light sources and screens emit light (prevents a
  robot's glowing eyes or ambient light from leaking onto people when several references are used).
- If the prompt has a "Continuity:" line, every fact in it must appear in the output: time of day (a night shot
  is visibly night: dark sky, artificial lights), weather, lighting, and who holds which prop.
- One-of-a-kind things the prompt mentions appear once (each character once; a planet or the sun once). Never add
  objects, planets or scenery that the prompt does not mention.
- Keep the 5-10 second action achievable in one continuous shot.
- Timing: the speaker starts the line within the first second of the shot and finishes it at least one second
  before the shot ends; after the line there is only a short silent reaction.
{ref_rules}"""

FMT_T2VA = "integrated_multimodal_description: [Shot 1] ...\n\noverall_soundscape: ...\n\nnon_diegetic_music: N/A"
FMT_REF = ("subject_definitions:\n<Subject 1> is the ... in <Picture 1>, ...\n\nsummary:\n[reference generation] ...\n\n"
           "retention_analysis:\n<Subject 1> (appears in [Shot 1]): fully_preserved - ...; the plain background of the "
           "reference picture is not used.\n\ndetailed_description:\nThe target video uses a realistic cinematic style with "
           "... lighting. No subtitles, captions, or overlaid text appear on screen.\n[Shot 1] ...\n\n"
           "overall_soundscape:\n...\n\nnon_diegetic_music:\nN/A")
REF_RULES = ("- Reference pictures: <Picture N> is the reference image of the N-th listed character. Define "
             "<Subject N> from <Picture N> with its appearance, mark it fully_preserved, and refer to it as <Subject N> "
             "everywhere (speaker IDs attach to subjects, e.g. <Subject 1> (S1)). Do not reuse the picture backgrounds.\n"
             "- Voice references: if a character has \"voice\": \"<Audio N>\", add the line \"<Audio N> is the voice-timbre "
             "reference for <Subject K> (S1).\" to subject_definitions, \"<Audio N>: reference - its vocal timbre guides "
             "<Subject K>'s dialogue without copying the original signal.\" to retention_analysis, and when that subject "
             "speaks write \"<Subject K> (S1), using the voice timbre referenced from <Audio N>, says: <markup>\".")


def _llm():
    from openai import OpenAI
    return OpenAI(api_key=Config.LLM_API_KEY or "EMPTY", base_url=Config.LLM_BASE_URL)


def rewrite(prompt: str, dialogue, speaker, voice, subjects) -> str:
    ref = bool(subjects)
    # A line whose speaker is not a referenced on-screen character (radio, PA speaker, narrator) is an
    # off-screen voice: on-screen characters must keep their lips closed, or H3 lip-syncs it to them.
    on_screen = {s.get("name") for s in subjects}
    off_screen = bool(dialogue) and (not speaker or speaker not in on_screen)
    user = {"shot_description": prompt, "duration_hint_seconds": None,
            "dialogue": {"line": dialogue, "speaker": speaker or "unseen voice (radio / loudspeaker)", "voice": voice,
                         "off_screen": off_screen,
                         "required_markup": f"<d>[{LANG}] {dialogue.strip()}</d>",
                         **({"instruction": "This line comes from an unseen source. Write it like this example: "
                             "'A calm female voice from the console speaker (S1) says in an off-screen voiceover: "
                             "[required_markup], while every on-screen character's lips remain completely closed.' "
                             "Describe the actual voice instead of the example voice."} if off_screen else {})} if dialogue else None,
            "reference_characters": [{"picture": f"<Picture {i + 1}>", "name": s.get("name"), "appearance": EYE_LIGHT.sub("", s.get("appearance") or ""),
                                      **({"voice": s["voice_tag"]} if s.get("voice_tag") else {})}
                                     for i, s in enumerate(subjects)] or None}
    sys_p = REWRITE_SYSTEM.format(fmt=FMT_REF if ref else FMT_T2VA, lang=LANG, ref_rules=REF_RULES if ref else "")
    r = _llm().chat.completions.create(model=Config.MODEL_NAME, temperature=0.3, max_tokens=1500,
                                       messages=[{"role": "system", "content": sys_p},
                                                 {"role": "user", "content": json.dumps(user, ensure_ascii=False)}])
    out = r.choices[0].message.content.strip()
    out = re.sub(r"^```\w*\n|\n```$", "", out).strip()
    return validate(out, dialogue, ref, speaker, voice, subjects, source=prompt)


def validate(text: str, dialogue, ref: bool, speaker=None, voice=None, subjects=(), source: str = "") -> str:
    """Deterministic guards: exact line inside <d>, no <d> when silent, no-captions clause present."""
    tags = list(re.finditer(r"<d>\s*\[[^\]]+\]\s*(.*?)</d>", text, flags=re.S))
    if dialogue:
        line = dialogue.strip()
        if tags:
            first = tags[0]
            text = text[:first.start()] + f"<d>[{LANG}] {line}</d>" + text[first.end():]
            for t in list(re.finditer(r"<d>.*?</d>", text, flags=re.S))[1:]:
                text = text.replace(t.group(0), "")
        else:
            anchor = "detailed_description:" if ref else "integrated_multimodal_description:"
            i = text.find("[Shot 1]"); i = i if i >= 0 else text.find(anchor)
            end = text.find("\n\noverall_soundscape")
            who = "The speaker"
            for n, sbj in enumerate(subjects or []):
                if speaker and sbj.get("name") == speaker:
                    who = f"<Subject {n + 1}>"
            desc = f", {voice}," if voice else ""
            if who == "The speaker":  # not an on-screen referenced character -> off-screen voice
                text = (text[:end] + f" An unseen voice{desc} (S1) says in an off-screen voiceover: <d>[{LANG}] {line}</d> "
                        "while every on-screen character's lips remain completely closed." + text[end:])
            else:
                text = text[:end] + f" {who} (S1){desc} says: <d>[{LANG}] {line}</d> and then closes their lips." + text[end:]
    else:
        text = re.sub(r"<d>.*?</d>", "", text, flags=re.S)
    off = bool(dialogue) and not (speaker and speaker in {x.get("name") for x in (subjects or [])})
    if off and "lips remain completely closed" not in text:   # an off-screen line: nobody on screen lip-syncs it
        end = text.find("\n\noverall_soundscape")
        end = end if end >= 0 else len(text)
        text = (text[:end] + " The line is an off-screen voice; every on-screen character's lips remain completely "
                "closed while it is heard." + text[end:])
    text = re.sub(r"<style sentence>\s*", "The target video uses a realistic cinematic style. ", text)
    text = re.sub(r"<(the voice|voice|speaker)>", "An unseen voice", text).replace("[required_markup]", "")
    if "no legible lettering" not in text:
        k0 = "detailed_description:\n" if ref else "integrated_multimodal_description: "
        text = text.replace(k0, k0 + "Any signs, displays and labels are out of focus, so no legible lettering appears. ", 1)
    if "No subtitles, captions" not in text:
        key = "detailed_description:\n" if ref else "integrated_multimodal_description: "
        text = text.replace(key, key + "No subtitles, captions, or overlaid text appear on screen. ", 1)
    # light-in-the-eyes wording ("eyes reflecting the amber lights") makes H3 render glowing human eyes: drop it
    text = EYE_LIGHT.sub("", text)
    # rules the model kept breaking even when the system prompt asked: enforce them in the prompt text itself
    key = "detailed_description:\n" if ref else "integrated_multimodal_description: "
    tod = re.search(r"Continuity: It is (dawn|day|dusk|night)(, ([^.]*))?\.", source or "")
    if tod and tod.group(1) not in text.lower():
        lead = {"night": "It is night: the sky outside is dark and the scene is lit only by artificial lights",
                "dusk": "It is dusk, with low warm light", "dawn": "It is dawn, with pale early light",
                "day": "It is daytime"}[tod.group(1)]
        text = text.replace(key, key + lead + (f", {tod.group(3)}" if tod.group(3) else "") + ". ", 1)
    if "eyes look natural" not in text and re.search(r"\b(she|he|woman|man|engineer|person|girl|boy)\b", text, re.I):
        text = text.replace(key, key + "Every human's eyes look natural, dark and non-glowing. ", 1)
    if re.search(r"\bEarth\b", source or "") and re.search(r"\bEarth\b", text) and "single Earth" not in text:
        text = text.replace(key, key + "Only a single Earth is visible, never two. ", 1)
    return text


EYE_LIGHT = re.compile(r"(,\s*|\s+)(with\s+)?(her|his|their)?\s*eyes\s+(reflecting|glowing|lit|catching|shining|gleaming|"
                       r"illuminated)[^,.;]*", re.I)


def voice_ref(image):
    """voice.wav beside a character reference image, if any (character_list/<Name>/voice.wav)."""
    if not image:
        return None
    p = Path(image) if Path(image).is_absolute() else ROOT / image
    for v in (p.with_name(p.stem + ".voice.wav"), p.parent / "voice.wav"):
        if v.exists() and (v.name != "voice.wav" or p.parent.name not in ("references",)):
            return str(v)
    return None


def upload_ref(local: str) -> str:
    p = Path(local)
    if not p.is_absolute():
        p = ROOT / p
    h = hashlib.sha1(p.read_bytes()).hexdigest()[:16]
    remote = f"{REF_REMOTE_DIR.rstrip('/')}/{h}{p.suffix or '.png'}"
    if REF_SSH_HOST:
        subprocess.run(["ssh", "-o", "BatchMode=yes", REF_SSH_HOST, f"mkdir -p {REF_REMOTE_DIR}"], check=True)
        subprocess.run(["scp", "-q", "-o", "BatchMode=yes", str(p), f"{REF_SSH_HOST}:{remote}"], check=True)
    return "file://" + remote


def _post(url, body):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))


def create(fields: dict, upload: bytes = None) -> dict:
    extra = {k: v for k, v in fields.items()}
    prompt = fields.get("prompt", "")
    dialogue, speaker, voice = extra.get("dialogue"), extra.get("speaker"), extra.get("voice_instructions")
    subjects = [s for s in (extra.get("reference_subjects") or []) if s.get("image")]
    if not subjects and upload:  # plain I2V-style reference without metadata
        tmp = LOG_DIR / f"upload_{uuid.uuid4().hex[:8]}.png"; tmp.write_bytes(upload)
        subjects = [{"image": str(tmp), "name": "the main character", "appearance": ""}]
    dur = float(extra.get("duration") or fields.get("seconds") or 5)
    if dialogue:  # leave room for the whole line + a beat: ~4 chars/s plus lead-in and reaction
        dur = max(dur, len(re.sub(r"[\s，。？！、,.?!…—]", "", dialogue)) / 4.0 + 1.8)
    dur = max(4.0, min(15.0, round(dur)))
    # voice timbre references: <character_list>/<Name>/voice.wav next to the reference image; only the speaker's
    # voice is attached (one <Audio 1>), so the line is voiced consistently across shots
    audio_conds = []
    for sbj in subjects:
        if not (speaker and sbj.get("name") == speaker):
            continue
        v = voice_ref(sbj.get("image")) or cast_voice(sbj, dialogue, voice)
        if v:
            sbj["voice_tag"] = "<Audio 1>"; audio_conds.append(v)
        break
    # keyframe-first: the shot's approved opening frame. Dialogue shots keep Ref2VA (character sheets + voice) and get
    # the frame as one more reference picture; silent shots start from it as the first frame (FL2VA).
    kf = extra.get("keyframe")
    kf = kf if kf and (Path(kf).exists() or (ROOT / kf).exists()) else None
    # who speaks: an on-screen referenced character, or an off-screen voice (radio, loudspeaker, narrator). Ref2VA
    # lip-syncs a line to whoever is on screen, so an off-screen line is rendered FL2VA from the keyframe with the
    # line as a voiceover and every on-screen mouth closed (EchoStation: Earth's radio reply was spoken on camera).
    on_screen_speaker = bool(dialogue) and bool(speaker) and speaker in {x.get("name") for x in subjects}
    two_pass = TWO_PASS and bool(kf) and on_screen_speaker
    off_screen_line = bool(dialogue) and not on_screen_speaker
    fl2va_first = bool(kf) and (not dialogue or two_pass or off_screen_line)
    if two_pass:   # pass 1: the silent take from the keyframe; the line is added by pass 2 (see status())
        h3_prompt = rewrite(prompt + SILENT_TAKE, None, None, None, [])
    else:   # an off-screen line on FL2VA keeps the line: rewrite() writes it as a voiceover (no subjects -> off-screen)
        h3_prompt = rewrite(prompt, dialogue, speaker if on_screen_speaker else None, voice,
                            [] if fl2va_first else subjects)
    if kf and not fl2va_first and subjects:
        k = len(subjects) + 1
        line = (f"<Picture {k}> is the opening frame of this shot (not a character): the video starts from its "
                f"composition, set, lighting and the characters' positions.")
        h3_prompt = h3_prompt.replace("\n\nsummary:", f"\n{line}\n\nsummary:", 1) if "\n\nsummary:" in h3_prompt \
            else f"{line}\n{h3_prompt}"
    kf_end = None
    if fl2va_first:   # pin both ends to checked frames: the start frame, and the end derived from it by the camera move
        kf_end = end_frame(kf, prompt, dur)
        h3_prompt = ("How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the "
                     f"0.00-second mark of the target video; Picture 2 (from Shot 1) aligns with the {dur:.2f}-second mark "
                     "of the target video.\n\n" + h3_prompt)
    body = {"model": "MiniMaxAI/MiniMax-H3", "prompt": h3_prompt, "seconds": int(dur), "num_outputs_per_prompt": 1,
            "num_inference_steps": STEPS, "flow_shift": 12.0, "audio_flow_shift": 3.0,
            "target": {"short_edge": 768, "aspect_ratio": "16:9", "duration_seconds": dur}}
    if extra.get("seed") is not None:
        body["seed"] = int(extra["seed"])
    final = str(extra.get("tier", "")).lower() == "final" and (FINAL_FL2VA_URLS or FINAL_REF2VA_URLS)
    if final:
        body["num_inference_steps"] = FINAL_STEPS
    pool = lambda draft, fin: (fin or draft) if final else draft
    if fl2va_first:
        body.update(task="fl2va", conditions=[{"type": "image", "uri": upload_ref(kf), "role": "keyframe", "frame_index": 0},
                                              {"type": "image", "uri": upload_ref(kf_end), "role": "keyframe", "frame_index": -1}])
        base = pick(pool(FL2VA_URLS, FINAL_FL2VA_URLS))
    elif subjects:
        body.update(task="ref2va", conditions=[{"type": "image", "uri": upload_ref(s["image"]), "role": "reference"} for s in subjects]
                    + ([{"type": "image", "uri": upload_ref(kf), "role": "reference"}] if kf else [])
                    + [{"type": "audio", "uri": upload_ref(v), "role": "reference"} for v in audio_conds])
        base = pick(pool(REF2VA_URLS, FINAL_REF2VA_URLS))
    else:
        body.update(task="t2va", conditions=[]); base = pick(pool(FL2VA_URLS, FINAL_FL2VA_URLS))
    try:
        job = _post(f"{base}/videos", body)
    except Exception:
        release(base); raise
    pid = "h3_" + uuid.uuid4().hex[:12]
    spk_img = next((x["image"] for x in subjects if speaker and x.get("name") == speaker), None)
    with _LOCK:
        JOBS[pid] = {"base": base, "h3_id": job["id"],
                     "harvest": (spk_img, dialogue) if (dialogue and spk_img and not audio_conds) else None}
        if two_pass:
            JOBS[pid]["pass2"] = {"subjects": subjects, "audio": audio_conds, "dialogue": dialogue, "speaker": speaker,
                                  "voice": voice, "seconds": int(dur), "target": body["target"],
                                  "seed": body.get("seed"), "final": bool(final)}
    (LOG_DIR / f"{pid}.json").write_text(json.dumps({"in": {k: v for k, v in fields.items()}, "h3_request": body},
                                                    ensure_ascii=False, indent=1))
    print(f"[h3_proxy] {pid} -> {base.split(':')[-1].split('/')[0]} {body['task']} {dur:.0f}s dialogue={bool(dialogue)} "
          f"keyframe={'first-frame' if fl2va_first else ('reference' if kf else 'none')}{' two-pass' if two_pass else ''}"
          f"{' FINAL ' + str(FINAL_STEPS) + ' steps' if final else ''}", flush=True)
    return {"id": pid, "object": "video", "status": "queued", "model": fields.get("model", "minimax-h3")}


SHEET = ("integrated_multimodal_description: [Shot 1] Live-action, cinematic, photorealistic. {kind} {desc} The camera is "
         "locked off and nothing moves except a slow breath. {eyes}Nobody speaks. No subtitles, captions, or overlaid "
         "text appear on screen.\n\noverall_soundscape: Quiet room tone.\n\nnon_diegetic_music: N/A")


def _wait(base: str, h3_id: str, timeout: float = 900) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = json.load(urllib.request.urlopen(f"{base}/videos/{h3_id}", timeout=60))
        if st.get("status") == "completed":
            return
        if st.get("status") == "failed":
            raise RuntimeError(f"H3 job failed: {st.get('error')}")
        time.sleep(3)
    raise TimeoutError("H3 job timed out")


_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
        "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70}


def age_anchor(desc: str) -> str:
    """Video models under-age characters described as 'small' or 'delicate'; restate the written age as body
    proportions they follow. Generic by age group, never story-specific."""
    m = re.search(r"\b(\d{1,2}|[a-z]+)[- ]year[- ]old\b", desc, re.I) or re.search(r"\b(?:early|mid|late)[- ](\d0)s\b", desc, re.I)
    if not m:
        return ""
    w = m.group(1).lower()
    n = int(w) if w.isdigit() else _NUM.get(w)
    if not n:
        return ""
    if n <= 6:
        return f"A small child of about {n}."
    if n <= 12:
        return f"A child of about {n}, school-age proportions."
    if n <= 19:
        return (f"A {n}-year-old teenager of high-school age: adolescent body proportions and height close to an adult, "
                f"a teenage face, clearly not a small child.")
    if n <= 59:
        return f"An adult of about {n}, adult proportions."
    return f"An older adult of about {n}, with the signs of age that brings."


def image(fields: dict) -> dict:
    """/v1/images/generations on top of H3 text-to-video: render a 4 s locked-off shot and return one frame.
    Character sheets: a still subject, waist-up, plain studio background. Locations ("establishing" prompts): the
    empty set. Used by ArtDepartment.generate_references when no image model is deployed."""
    from src.adapters.t2i_client import split_negative
    prompt, _ = split_negative(fields.get("prompt", ""))
    prompt = EYE_LIGHT.sub("", prompt).strip()
    location = "establishing" in prompt.lower() or "no people" in prompt.lower()
    kind = ("An empty establishing shot of the location, no people:" if location else
            "A character reference shot: one person (or creature/robot) standing upright, centered, waist-up, awake with "
            "eyes open, facing the camera with a neutral expression and arms relaxed, evenly lit against a plain "
            "light-grey studio background. They do not act out any story moment (not sleeping, lying, bending, running "
            "or holding story props). Appearance:")
    eyes = "" if location else "Every human's eyes look natural, dark and non-glowing. "
    anchor = "" if location else age_anchor(prompt)
    desc = prompt[:1500]
    body = {"model": "MiniMaxAI/MiniMax-H3", "prompt": SHEET.format(kind=kind, desc=(anchor + " " + desc).strip(), eyes=eyes),
            "seconds": 4, "num_outputs_per_prompt": 1, "num_inference_steps": STEPS, "flow_shift": 12.0,
            "audio_flow_shift": 3.0, "task": "t2va", "conditions": [],
            "target": {"short_edge": 768, "aspect_ratio": "16:9", "duration_seconds": 4.0}}   # H3 accepts 4-15 s
    import random
    seed0 = fields.get("seed") or (fields.get("extra_body") or {}).get("seed")
    body["seed"] = int(seed0) if seed0 is not None else random.randint(1, 10 ** 6)   # repeated calls must differ
    import base64
    last_why = ""
    for attempt in range(4):   # the sheet anchors identity for every shot: validate it, re-roll if no frame passes
        if attempt:
            body["seed"] = int(body["seed"]) + 1000 * attempt
            if last_why:   # prompt repair: rewrite the appearance from what the check rejected, then re-render
                desc = fix_sheet_prompt(desc, last_why)
                print(f"[h3_proxy] sheet prompt rewritten: {desc[:160]}", flush=True)
                body["prompt"] = SHEET.format(kind=kind, desc=(anchor + " " + desc).strip(), eyes=eyes)
        b = pick(FL2VA_URLS)
        try:
            job = _post(f"{b}/videos", body)
            _wait(b, job["id"])
            data = urllib.request.urlopen(f"{b}/videos/{job['id']}/content", timeout=300).read()
        finally:
            release(b)
        pid = "img_" + uuid.uuid4().hex[:12]
        (LOG_DIR / f"{pid}.json").write_text(json.dumps({"in": fields, "h3_request": body}, ensure_ascii=False, indent=1))
        print(f"[h3_proxy] {pid} -> image ({'location' if location else 'character'}) attempt {attempt}", flush=True)
        mp4 = LOG_DIR / f"{pid}.mp4"
        mp4.write_bytes(data)
        frames = []
        for k, t in enumerate((0.6, 1.5, 2.4, 3.3)):
            f = LOG_DIR / f"{pid}_{k}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(mp4), "-frames:v", "1", str(f)], check=True)
            frames.append(f)
        chosen = frames[1] if location else pick_sheet_frame(frames, prompt)
        last_why = _LAST_SHEET_WHY.get("why", "")
        if chosen is not None:
            return {"created": int(time.time()), "data": [{"b64_json": base64.b64encode(chosen.read_bytes()).decode()}]}
        print(f"[h3_proxy] {pid}: no frame is a usable character sheet, re-rolling", flush=True)
    raise RuntimeError("no usable character sheet after 4 attempts")


SHEET_CHECK = ("These {n} images are frames of a character reference sheet (image 1..{n}). A usable sheet shows exactly one "
               "subject, upright (standing or sitting straight), awake with eyes open, facing the camera, head and upper "
               "body fully in frame, neutral pose, plain background, AND matches the description: same apparent age group "
               "(child / teenager / adult / elderly), gender and species, and the described outfit. Estimate the age you "
               "see. Answer ONLY JSON: {{\"apparent_age\": \"...\", \"matches_description\": true/false, "
               "\"usable\": [frame numbers that qualify], \"best\": frame number or 0 if none, \"why\": \"short\"}}")


_LAST_SHEET_WHY = {}

SHEET_FIX = """A video model rendered this character description wrong. The check said: {why}
Rewrite the appearance description so the model renders what the character is meant to be (their written age, gender,
species and outfit). Remove wording that pulls the render the wrong way (for an under-aged render: small, delicate,
cute, petite, little, holding a school bag in both hands; for an over-aged one: weathered, tired), and add concrete
visual cues the model follows: height relative to adults, face shape and maturity, body proportions, hairstyle, how the
outfit fits. Keep the outfit, colours and hairstyle. Output ONLY the rewritten description, one paragraph, English.

Description:
{desc}"""


def fix_sheet_prompt(desc: str, why: str) -> str:
    from openai import OpenAI
    try:
        r = OpenAI(api_key=Config.LLM_API_KEY or "EMPTY", base_url=Config.LLM_BASE_URL).chat.completions.create(
            model=Config.MODEL_NAME, temperature=0.4, max_tokens=400,
            messages=[{"role": "user", "content": SHEET_FIX.format(why=why, desc=desc[:1500])}])
        out = (r.choices[0].message.content or "").strip()
        return out or desc
    except Exception as e:
        print(f"[h3_proxy] sheet prompt fix unavailable ({e})", flush=True)
        return desc


def pick_sheet_frame(frames, desc):
    import base64
    from openai import OpenAI
    content = [{"type": "text", "text": SHEET_CHECK.format(n=len(frames)) + f" Subject: {desc[:300]}"}]
    for f in frames:
        content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(f.read_bytes()).decode()}})
    try:
        r = OpenAI(api_key=Config.LLM_API_KEY or "EMPTY", base_url=Config.LLM_BASE_URL).chat.completions.create(
            model=Config.MODEL_NAME, temperature=0, max_tokens=120, response_format={"type": "json_object"},
            messages=[{"role": "user", "content": content}])
        v = json.loads(r.choices[0].message.content)
    except Exception as e:
        print(f"[h3_proxy] sheet check unavailable ({e}); using the middle frame", flush=True)
        return frames[1]
    best = int(v.get("best") or 0)
    if v.get("matches_description") is False:   # e.g. a toddler for a 16-year-old: every shot would inherit it
        best = 0
    _LAST_SHEET_WHY["why"] = (f"it looked {v.get('apparent_age')}, not as described; {v.get('why', '')}"
                              if best == 0 else "")
    print(f"[h3_proxy] sheet check: best={best} age={v.get('apparent_age')} match={v.get('matches_description')} "
          f"usable={v.get('usable')} ({v.get('why', '')[:80]})", flush=True)
    return frames[best - 1] if 1 <= best <= len(frames) else None


_CAST_LOCK = threading.Lock()


def cast_voice(sbj: dict, line: str, voice) -> str:
    """Voice casting before a speaker's first shot: a short single-person close-up of them saying the line, from
    which the canon voice reference is cut. Every dialogue shot of that speaker, the first included, is then
    conditioned on the same <Audio 1>, instead of the first shot inventing a timbre the later ones copy."""
    with _CAST_LOCK:
        if voice_ref(sbj["image"]):
            return voice_ref(sbj["image"])
        try:
            one = dict(sbj); one.pop("voice_tag", None)
            # a short line gives a short, unstable timbre reference: pad the casting take with a neutral sentence
            cast_line = line if len(re.sub(r"[\s，。？！、,.?!…—]", "", line or "")) >= 12 else f"{line}嗯，我想一想，对，就是这样。"
            prompt = (f"Close-up of {sbj.get('name')} alone in a quiet room, facing the camera, saying one line in their "
                      f"natural voice, then holding still.")
            body = {"model": "MiniMaxAI/MiniMax-H3", "prompt": rewrite(prompt, cast_line, sbj.get("name"), voice, [one]),
                    "seconds": 6, "num_outputs_per_prompt": 1, "num_inference_steps": STEPS, "flow_shift": 12.0,
                    "audio_flow_shift": 3.0, "task": "ref2va",
                    "conditions": [{"type": "image", "uri": upload_ref(sbj["image"]), "role": "reference"}],
                    "target": {"short_edge": 768, "aspect_ratio": "16:9", "duration_seconds": 6.0}}
            b = pick(REF2VA_URLS)
            try:
                job = _post(f"{b}/videos", body)
                print(f"[h3_proxy] casting voice for {sbj.get('name')} on {b}", flush=True)
                _wait(b, job["id"])
                data = urllib.request.urlopen(f"{b}/videos/{job['id']}/content", timeout=300).read()
            finally:
                release(b)
            clip = LOG_DIR / f"cast_{uuid.uuid4().hex[:8]}.mp4"; clip.write_bytes(data)
            harvest_voice(clip, sbj["image"], line)
        except Exception as e:
            print(f"[h3_proxy] voice casting failed for {sbj.get('name')}: {type(e).__name__}: {e}", flush=True)
        return voice_ref(sbj["image"])


def harvest_voice(clip: Path, image: str, line: str) -> None:
    """Canon voice memory: the first delivered line of a speaker without a voice reference becomes their
    <image stem>.voice.wav (speech span only, loudness-normalised), so later shots reuse the same timbre."""
    p = Path(image) if Path(image).is_absolute() else ROOT / image
    out = p.with_name(p.stem + ".voice.wav")
    if out.exists() or voice_ref(image):
        return
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(clip), "-af", "silencedetect=n=-35dB:d=0.35", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(clip)],
                               capture_output=True, text=True).stdout.strip() or 0)
    # whole delivered line: from the end of leading silence to the start of trailing silence, inner pauses kept
    t0 = ends[0] if ends and starts and starts[0] < 0.05 else 0.0
    trailing = [st for i, st in enumerate(starts) if st > t0 and (i >= len(ends) or ends[i] >= dur - 0.05)]
    t1 = trailing[0] if trailing else dur
    if t1 - t0 < 2.0:
        print(f"[h3_proxy] voice memory skipped: {t1 - t0:.1f}s of speech in {clip.name}", flush=True)
        return
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, t0 - 0.05):.2f}", "-to", f"{min(dur, t1 + 0.1):.2f}",
                    "-i", str(clip), "-ac", "1", "-ar", "24000", "-af", "loudnorm=I=-20", str(out)], check=True)
    out.with_suffix(".txt").write_text(line)
    print(f"[h3_proxy] voice memory: {out.name} ({t1 - t0:.1f}s) from {clip.name}", flush=True)


def end_frame(kf: str, prompt: str, dur: float) -> str:
    """Last frame for a silent keyframe shot, derived deterministically from the checked first frame: a push-in /
    dolly-in / zoom-in becomes a centred crop (the camera moved closer), anything else keeps the frame. Without a
    pinned end the 8-step model drifts (EchoStation: a second Earth appeared mid-shot)."""
    from PIL import Image
    p = Path(kf) if Path(kf).is_absolute() else ROOT / kf
    im = Image.open(p).convert("RGB")
    low = (prompt or "").lower()
    if re.search(r"push(es|ing)?[ -]in|dolly(ing)?[ -]in|zoom(s|ing)?[ -]in|moves? (in|closer)|pushes? toward", low):
        k = 0.82 if dur >= 5 else 0.88
        w, h = im.size; cw, ch = int(w * k), int(h * k)
        im = im.crop(((w - cw) // 2, (h - ch) // 2, (w + cw) // 2, (h + ch) // 2)).resize((w, h), Image.LANCZOS)
    out = LOG_DIR / f"end_{p.stem}_{uuid.uuid4().hex[:6]}.png"
    im.save(out)
    return str(out)


def edit_prompt(p2: dict) -> str:
    """Pass 2 of a two-pass dialogue shot: Ref2VA video editing that keeps <Video 1> and adds the spoken line."""
    defs = [f"<Subject {i}> is {('the ' + x['appearance'].rstrip('.')) if x.get('appearance') else 'the character'} in "
            f"<Picture {i}>; this is {x.get('name') or 'a character'}." for i, x in enumerate(p2["subjects"], 1)]
    spk = next((f"<Subject {i}>" for i, x in enumerate(p2["subjects"], 1) if x.get("name") == p2.get("speaker")),
               "<Subject 1>")
    voice_line = f"<Audio 1> is the voice timbre reference for {spk}'s voice.\n" if p2["audio"] else ""
    voice_ref = ", using the voice timbre referenced from <Audio 1>" if p2["audio"] else ""
    return ("subject_definitions:\n" + "\n".join(defs) + "\n<Video 1> is the source video for the editing task.\n"
            + voice_line +
            f"\nsummary:\n[video editing + audio reference] The target video is an edited version of <Video 1>. The "
            f"edit animates {spk}'s face to speak the line; everything else in <Video 1> is kept exactly: framing, "
            f"camera movement, set, lighting, the view through the windows, and every character's position and motion."
            f"\n\nretention_analysis:\n<Video 1> (source video editing): fully_preserved - the original framing, camera "
            f"movement, set, lighting, view through the windows and all characters are maintained; only {spk}'s mouth "
            f"is newly animated to speak.\n"
            + (f"<Audio 1>: reference - the target audio references the voice timbre of <Audio 1> for {spk}'s spoken "
               f"line.\n" if p2["audio"] else "") +
            f"\ndetailed_description:\nThe target video is in realistic photographic style.\n[Shot 1] The shot is "
            f"<Video 1>, unchanged. {spk} (S1) speaks{voice_ref}: <d>[{LANG}] {p2['dialogue']}</d> Exactly as the voice "
            f"stops, the lips close and the jaw stops moving; the rest of the shot continues as in <Video 1>. No "
            f"subtitles, captions, or overlaid text appear on screen.\n\noverall_soundscape:\n{spk}'s clear spoken line"
            f"{' in the voice timbre of <Audio 1>' if p2['audio'] else ''}"
            f"{(' (' + p2['voice'].splitlines()[0] + ')') if p2.get('voice') else ''}, over the quiet ambient sound of "
            f"<Video 1>.\n\nnon_diegetic_music:\nN/A")


def start_pass2(pid: str, j: dict) -> None:
    """Pass 1 is done: upload its clip as <Video 1> and submit the Ref2VA edit that adds the line."""
    p2 = j.pop("pass2")
    clip = LOG_DIR / f"{pid}_pass1.mp4"
    clip.write_bytes(urllib.request.urlopen(f"{j['base']}/videos/{j['h3_id']}/content", timeout=300).read())
    body = {"model": "MiniMaxAI/MiniMax-H3", "prompt": edit_prompt(p2), "seconds": p2["seconds"],
            "num_outputs_per_prompt": 1, "num_inference_steps": FINAL_STEPS if p2["final"] else STEPS,
            "flow_shift": 12.0, "audio_flow_shift": 3.0, "target": p2["target"], "task": "ref2va",
            "conditions": [{"type": "image", "uri": upload_ref(x["image"]), "role": "reference"} for x in p2["subjects"]]
            + [{"type": "video", "uri": upload_ref(str(clip)), "role": "reference"}]
            + [{"type": "audio", "uri": upload_ref(v), "role": "reference"} for v in p2["audio"]]}
    if p2.get("seed") is not None:
        body["seed"] = p2["seed"]
    base = pick(FINAL_REF2VA_URLS if (p2["final"] and FINAL_REF2VA_URLS) else REF2VA_URLS)
    try:
        job = _post(f"{base}/videos", body)
    except Exception:
        release(base); raise
    if not j.get("released"):
        release(j["base"])
    j.update(base=base, h3_id=job["id"], released=False)
    (LOG_DIR / f"{pid}_pass2.json").write_text(json.dumps({"h3_request": body}, ensure_ascii=False, indent=1))
    print(f"[h3_proxy] {pid} pass 2 -> {base.split(':')[-1].split('/')[0]} ref2va edit of the silent take", flush=True)


def status(pid: str) -> dict:
    j = JOBS.get(pid)
    if not j:
        return {"id": pid, "status": "failed", "error": {"message": "unknown id"}}
    if j.get("starting"):   # pass 2 is being submitted: never report the silent take as the result
        return {"id": pid, "object": "video", "status": "in_progress", "error": None}
    st = json.load(urllib.request.urlopen(f"{j['base']}/videos/{j['h3_id']}", timeout=60))
    s = st.get("status", "")
    s = {"pending": "queued", "running": "in_progress", "processing": "in_progress"}.get(s, s)
    if s == "completed" and j.get("pass2"):   # two-pass dialogue shot: the silent take is ready, add the line
        with _LOCK:
            go = j.get("pass2") is not None and not j.get("starting")
            j["starting"] = True
        if go:
            try:
                start_pass2(pid, j)
            finally:
                j["starting"] = False
        return {"id": pid, "object": "video", "status": "in_progress", "error": None}
    if s in ("completed", "failed") and not j.get("released"):
        j["released"] = True; release(j["base"])
    err = st.get("error")
    return {"id": pid, "object": "video", "status": s, "error": ({"message": str(err)} if err else None)}


def parse_multipart(ctype: str, raw: bytes):
    msg = email.parser.BytesParser(policy=email.policy.HTTP).parsebytes(f"Content-Type: {ctype}\r\n\r\n".encode() + raw)
    fields, upload, cols = {}, None, {}
    for part in msg.iter_parts():
        name = part.get_param("name", header="content-disposition")
        data = part.get_payload(decode=True)
        if part.get_filename():
            upload = data
            continue
        val = data.decode("utf-8")
        try:
            val = json.loads(val)
        except Exception:
            pass
        key = re.sub(r"\[\]$", "", name)
        m = re.match(r"^(\w+)\[(\d+)\]\[(\w+)\]$", name)  # reference_subjects[0][image]
        mb = re.match(r"^(\w+)\[\]\[(\w+)\]$", name)        # reference_subjects[][image] (openai SDK form encoding)
        if mb:   # collect per field, assemble by index below (the SDK may emit field-major or item-major order)
            cols.setdefault(mb.group(1), {}).setdefault(mb.group(2), []).append(val)
        elif m:
            lst = fields.setdefault(m.group(1), []); i = int(m.group(2))
            while len(lst) <= i: lst.append({})
            lst[i][m.group(3)] = val
        elif name.endswith("[]") or re.match(r"^\w+\[\d+\]$", name):
            fields.setdefault(re.sub(r"\[\d*\]$", "", name), []).append(val)
        else:
            fields[key] = val
    for arr, by_field in cols.items():
        n = max(len(v) for v in by_field.values())
        fields[arr] = [{f: v[i] for f, v in by_field.items() if i < len(v)} for i in range(n)]
    return fields, upload


class H(BaseHTTPRequestHandler):
    def _send(self, code, obj=None, raw=None, ctype="application/json"):
        data = raw if raw is not None else json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(data)))
        self.end_headers(); self.wfile.write(data)

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        ctype = self.headers.get("Content-Type", "")
        if self.path.rstrip("/").endswith("/images/generations"):
            try:
                return self._send(200, image(json.loads(raw)))
            except Exception as e:
                print(f"[h3_proxy] image failed: {type(e).__name__}: {e}", flush=True)
                return self._send(500, {"error": {"message": f"{type(e).__name__}: {e}"}})
        if not self.path.rstrip("/").endswith("/videos"):
            return self._send(404, {"error": "not found"})
        try:
            fields, upload = parse_multipart(ctype, raw) if ctype.startswith("multipart/") else (json.loads(raw), None)
            self._send(200, create(fields, upload))
        except Exception as e:
            print(f"[h3_proxy] create failed: {type(e).__name__}: {e}", flush=True)
            self._send(500, {"error": {"message": f"{type(e).__name__}: {e}"}})

    def do_GET(self):
        m = re.match(r"^/v1/videos/([\w-]+)(/content)?", self.path)
        if not m:
            return self._send(200, {"status": "ok"}) if self.path.startswith("/health") else self._send(404, {"error": "not found"})
        pid, content = m.group(1), m.group(2)
        try:
            if content:
                if "variant=" in self.path:  # no spritesheet support -> client falls back to ffmpeg
                    return self._send(404, {"error": "no variant"})
                j = JOBS[pid]
                data = urllib.request.urlopen(f"{j['base']}/videos/{j['h3_id']}/content", timeout=300).read()
                if j.get("harvest"):
                    try:
                        tmp = LOG_DIR / f"{pid}.mp4"; tmp.write_bytes(data)
                        harvest_voice(tmp, *j["harvest"]); j["harvest"] = None
                    except Exception as e:
                        print(f"[h3_proxy] voice harvest skipped: {e}", flush=True)
                return self._send(200, raw=data, ctype="video/mp4")
            self._send(200, status(pid))
        except Exception as e:
            self._send(500, {"error": {"message": f"{type(e).__name__}: {e}"}})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    if not REF_REMOTE_DIR:
        print("[h3_proxy] warning: REF_REMOTE_DIR unset; reference images will not reach the H3 server", flush=True)
    print(f"[h3_proxy] listening on 127.0.0.1:{PORT}  FL2VA={FL2VA_URLS}  Ref2VA={REF2VA_URLS}  LLM={Config.LLM_BASE_URL}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
