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

FL2VA = os.getenv("H3_FL2VA_URL", "http://127.0.0.1:30010/v1").rstrip("/")
REF2VA = os.getenv("H3_REF2VA_URL", "http://127.0.0.1:30020/v1").rstrip("/")
STEPS = int(os.getenv("H3_STEPS", "8"))
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
- Human characters' eyes look natural and never glow; only light sources and screens emit light (prevents a
  robot's glowing eyes or ambient light from leaking onto people when several references are used).
- One-of-a-kind objects appear once: a single Earth, a single sun, a single moon, each character once. If a window
  shows the Earth, say "a single Earth".
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
    return validate(out, dialogue, ref, speaker, voice, subjects)


def validate(text: str, dialogue, ref: bool, speaker=None, voice=None, subjects=()) -> str:
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
    text = re.sub(r"<style sentence>\s*", "The target video uses a realistic cinematic style. ", text)
    text = re.sub(r"<(the voice|voice|speaker)>", "An unseen voice", text).replace("[required_markup]", "")
    if "No subtitles, captions" not in text:
        key = "detailed_description:\n" if ref else "integrated_multimodal_description: "
        text = text.replace(key, key + "No subtitles, captions, or overlaid text appear on screen. ", 1)
    # light-in-the-eyes wording ("eyes reflecting the amber lights") makes H3 render glowing human eyes: drop it
    text = EYE_LIGHT.sub("", text)
    # rules the model kept breaking even when the system prompt asked: enforce them in the prompt text itself
    key = "detailed_description:\n" if ref else "integrated_multimodal_description: "
    if "eyes look natural" not in text and re.search(r"\b(she|he|woman|man|engineer|person|girl|boy)\b", text, re.I):
        text = text.replace(key, key + "Every human's eyes look natural, dark and non-glowing. ", 1)
    if re.search(r"\bEarth\b", text) and "single Earth" not in text:
        text = text.replace(key, key + "Only a single Earth is visible, never two. ", 1)
    return text


EYE_LIGHT = re.compile(r"(,\s*|\s+)(with\s+)?(her|his|their)?\s*eyes\s+(reflecting|glowing|lit|catching|shining|gleaming|"
                       r"illuminated)[^,.;]*", re.I)


def voice_ref(image):
    """voice.wav beside a character reference image, if any (character_list/<Name>/voice.wav)."""
    if not image:
        return None
    p = Path(image) if Path(image).is_absolute() else ROOT / image
    v = p.parent / "voice.wav"
    return str(v) if v.exists() else None


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
        v = voice_ref(sbj.get("image"))
        if v and speaker and sbj.get("name") == speaker:
            sbj["voice_tag"] = "<Audio 1>"; audio_conds.append(v); break
    h3_prompt = rewrite(prompt, dialogue, speaker, voice, subjects)
    body = {"model": "MiniMaxAI/MiniMax-H3", "prompt": h3_prompt, "seconds": int(dur), "num_outputs_per_prompt": 1,
            "num_inference_steps": STEPS, "flow_shift": 12.0, "audio_flow_shift": 3.0,
            "target": {"short_edge": 768, "aspect_ratio": "16:9", "duration_seconds": dur}}
    if extra.get("seed") is not None:
        body["seed"] = int(extra["seed"])
    if subjects:
        body.update(task="ref2va", conditions=[{"type": "image", "uri": upload_ref(s["image"]), "role": "reference"} for s in subjects]
                    + [{"type": "audio", "uri": upload_ref(v), "role": "reference"} for v in audio_conds])
        base = REF2VA
    else:
        body.update(task="t2va", conditions=[]); base = FL2VA
    job = _post(f"{base}/videos", body)
    pid = "h3_" + uuid.uuid4().hex[:12]
    with _LOCK:
        JOBS[pid] = {"base": base, "h3_id": job["id"]}
    (LOG_DIR / f"{pid}.json").write_text(json.dumps({"in": {k: v for k, v in fields.items()}, "h3_request": body},
                                                    ensure_ascii=False, indent=1))
    print(f"[h3_proxy] {pid} -> {base.split(':')[-1].split('/')[0]} {body['task']} {dur:.0f}s dialogue={bool(dialogue)}", flush=True)
    return {"id": pid, "object": "video", "status": "queued", "model": fields.get("model", "minimax-h3")}


def status(pid: str) -> dict:
    j = JOBS.get(pid)
    if not j:
        return {"id": pid, "status": "failed", "error": {"message": "unknown id"}}
    st = json.load(urllib.request.urlopen(f"{j['base']}/videos/{j['h3_id']}", timeout=60))
    s = st.get("status", "")
    s = {"pending": "queued", "running": "in_progress", "processing": "in_progress"}.get(s, s)
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
        if not self.path.rstrip("/").endswith("/videos"):
            return self._send(404, {"error": "not found"})
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        ctype = self.headers.get("Content-Type", "")
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
                return self._send(200, raw=data, ctype="video/mp4")
            self._send(200, status(pid))
        except Exception as e:
            self._send(500, {"error": {"message": f"{type(e).__name__}: {e}"}})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    if not REF_REMOTE_DIR:
        print("[h3_proxy] warning: REF_REMOTE_DIR unset; reference images will not reach the H3 server", flush=True)
    print(f"[h3_proxy] listening on 127.0.0.1:{PORT}  FL2VA={FL2VA}  Ref2VA={REF2VA}  LLM={Config.LLM_BASE_URL}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
