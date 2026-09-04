#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Local media utilities on top of ffmpeg / ffprobe (no model calls).

    sample_frames()   frames for the VLM judge
    concat_clips()    cut the segment clips together into one film (fade-in on the first shot)

Every function returns None / [] instead of raising when ffmpeg is unavailable, so
the pipeline degrades to "clips only" rather than failing.
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional


def have_ffmpeg() -> bool:
    return bool(shutil.which("ffmpeg"))


def _run(cmd: List[str], timeout: int = 600) -> bool:
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=timeout)
        return True
    except Exception as e:  # missing binary, bad input, timeout
        err = getattr(e, "stderr", b"")
        print(f"      ⚠️  ffmpeg: {type(e).__name__} {err[-200:].decode(errors='ignore') if err else ''}".rstrip(), flush=True)
        return False


def probe_duration(path: Path) -> float:
    if not shutil.which("ffprobe"):
        return 0.0
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        return float(out or 0)
    except Exception:
        return 0.0


def has_audio_stream(path: Path) -> bool:
    if not shutil.which("ffprobe"):
        return False
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=30,
    ).stdout.strip()
    return bool(out)


def sample_frames(video_path: Path, prefix: Path, n: int = 4) -> List[Path]:
    """Sample `n` frames evenly; [] if ffmpeg is missing or fails."""
    if not have_ffmpeg() or not Path(video_path).exists():
        return []
    duration = probe_duration(video_path)
    fps = f"{n}/{duration:.3f}" if duration > 0 else "1"
    prefix.parent.mkdir(parents=True, exist_ok=True)
    ok = _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video_path), "-vf", f"fps={fps}",
               "-frames:v", str(n), "-q:v", "3", f"{prefix}_f%02d.jpg"], timeout=120)
    return sorted(prefix.parent.glob(f"{prefix.name}_f*.jpg")) if ok else []


def concat_clips(clips: List[Path], out_path: Path, fade_in: float = 0.0) -> Optional[Path]:
    """
    Cut the clips together in order. Every clip is normalised first (same codec,
    pixel format, sample rate; a silent track is added where a clip has none) so the
    concat is lossless afterwards. `fade_in` seconds are applied to the first clip.
    """
    clips = [Path(c) for c in clips if Path(c).exists()]
    if not clips or not have_ffmpeg():
        return None
    work = out_path.parent / f".{out_path.stem}_parts"
    work.mkdir(parents=True, exist_ok=True)
    parts: List[Path] = []
    for i, clip in enumerate(clips):
        part = work / f"{i:04d}.mp4"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(clip)]
        if not has_audio_stream(clip):
            cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000", "-shortest"]
        vf = f"fade=t=in:st=0:d={fade_in:.2f}" if (i == 0 and fade_in > 0) else "null"
        cmd += ["-map", "0:v:0", "-map", "1:a:0" if not has_audio_stream(clip) else "0:a:0",
                "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2",
                str(part)]
        if not _run(cmd):
            return None
        parts.append(part)
    listing = work / "list.txt"
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in parts), encoding="utf-8")
    ok = _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
               "-c", "copy", str(out_path)])
    return out_path if ok else None
