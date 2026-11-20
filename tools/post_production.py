#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
post_production: "Post Supervisor" pass over a rendered run -> <run>/media/film_post.mp4

  python tools/post_production.py <run_dir> [--no-subs] [--font <ttc>]

Uses shots/scene_blueprint_final.json (kept clips, dialogue) and qa_report.json (speech spans from tools/qa_report.py):
  - trims dead air on dialogue shots: keep <= LEAD s before the first word and <= TAIL s after the last
  - levels loudness per clip (dialogue -20 LUFS, ambience-only -30 LUFS), 60 ms audio fades at every cut
  - burns the dialogue line as a subtitle while it is spoken (Pillow-rendered PNG overlay; no ffmpeg drawtext needed)
  - fade in from black on the first shot, fade out (video + audio) on the last, final loudnorm -16 LUFS
Writes shots/scene_blueprint_post.json (clip paths -> processed clips) so qa_report can grade the result.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LEAD, TAIL = 0.4, 1.0
W, H, FPS = 1344, 768, 24
DEFAULT_FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"


def run(*a):
    subprocess.run([str(x) for x in a], check=True)


def duration(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout.strip() or 0)


def loudnorm_filter(src, t0, t1, target):
    """Two-pass loudnorm: measure the segment, then normalise linearly (single-pass loudnorm falls back to dynamic
    mode and lands several LU off on clips of a few seconds)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", str(src), "-vn", "-af",
                        f"loudnorm=I={target}:TP=-2:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    try:
        m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
        if float(m["input_i"]) < -70:   # silent clip
            raise ValueError
        return (f"loudnorm=I={target}:TP=-2:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    except (ValueError, KeyError):
        return f"loudnorm=I={target}:TP=-2:LRA=11"


def subtitle_png(text: str, out: Path, font_path: str):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(font_path, 34, index=2 if font_path.endswith(".ttc") else 0)
    tw = d.textlength(text, font=f); x0 = (W - tw) / 2; y = H - 70
    d.rounded_rectangle([x0 - 18, y - 30, x0 + tw + 18, y + 26], radius=8, fill=(0, 0, 0, 150))
    d.text((W / 2, y), text, font=f, fill=(245, 245, 240, 255), anchor="mm")
    im.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir"); ap.add_argument("--no-subs", action="store_true"); ap.add_argument("--font", default=DEFAULT_FONT)
    a = ap.parse_args()
    runp = Path(a.run_dir); post = runp / "media" / "post"; post.mkdir(parents=True, exist_ok=True)
    bp = json.loads((runp / "shots" / "scene_blueprint_final.json").read_text())
    qa = {s["shot"]: s for s in json.loads((runp / "qa_report.json").read_text())["shots"]} if (runp / "qa_report.json").exists() else {}
    outs = []
    n = len(bp["shots"])
    for i, s in enumerate(bp["shots"]):
        v = ((s.get("render_layer") or {}).get("video") or {})
        clip = (v.get("video_clip_paths") or [None])[0]
        if not clip:
            continue
        src = Path(clip) if Path(clip).is_absolute() else ROOT / clip
        d = duration(src); q = qa.get(s["shot_id"], {})
        dia = s["narrative_layer"].get("dialogue") or {}
        line = dia.get("text") if dia.get("has_dialogue") else None
        t0, t1 = 0.0, d
        span = q.get("speech_span")
        if line and span:
            lead, tail = span; speech_end = d - tail
            if lead > LEAD + 0.3:
                t0 = lead - LEAD
            if tail > TAIL + 0.3:
                t1 = min(d, speech_end + TAIL)
        seg_d = t1 - t0
        target = -20 if line else -30
        afilt = [loudnorm_filter(src, t0, t1, target), "aresample=48000", "afade=t=in:d=0.06", f"afade=t=out:st={max(0, seg_d - 0.06):.3f}:d=0.06"]
        vfilt = [f"scale={W}:{H}:force_original_aspect_ratio=decrease", f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2", f"fps={FPS}"]
        if i == 0:
            vfilt.append("fade=t=in:d=0.6")
        if i == n - 1:
            vfilt.append(f"fade=t=out:st={max(0, seg_d - 1.5):.3f}:d=1.5"); afilt[-1] = f"afade=t=out:st={max(0, seg_d - 1.5):.3f}:d=1.5"
        out = post / f"{i + 1:02d}_{s['shot_id']}.mp4"
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", src]
        if line and not a.no_subs:
            png = post / f"{i + 1:02d}_sub.png"; subtitle_png(line.strip(), png, a.font)
            s0 = max(0.0, (span[0] - t0) - 0.1) if span else 0.2
            s1 = min(seg_d, (d - span[1] - t0) + 0.3) if span else seg_d - 0.2
            cmd += ["-loop", "1", "-i", png, "-filter_complex",
                    f"[0:v]{','.join(vfilt)}[v];[v][1:v]overlay=0:0:enable='between(t,{s0:.2f},{s1:.2f})',format=yuv420p[o];"
                    f"[0:a]{','.join(afilt)}[a]", "-map", "[o]", "-map", "[a]", "-shortest"]
        else:
            cmd += ["-vf", ",".join(vfilt) + ",format=yuv420p", "-af", ",".join(afilt)]
        cmd += ["-ac", "2", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", out]
        run(*cmd)
        outs.append(out); v["video_clip_paths"] = [str(out)]
        print(f"[post] {s['shot_id']}: {d:.2f}s -> {seg_d:.2f}s{' +sub' if line and not a.no_subs else ''}", flush=True)
    lst = post / "concat.txt"; lst.write_text("".join(f"file '{p.resolve()}'\n" for p in outs))
    joined = post / "joined.mp4"
    run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined)
    film = runp / "media" / "film_post.mp4"
    run("ffmpeg", "-v", "error", "-y", "-i", joined, "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", film)
    (runp / "shots" / "scene_blueprint_post.json").write_text(json.dumps(bp, ensure_ascii=False, indent=1))
    print(f"[post] film: {film} ({duration(film):.1f}s)")


if __name__ == "__main__":
    main()
