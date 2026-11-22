#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Hard cuts inside one generated clip (the model sometimes renders two shots in one clip). ffmpeg scene scores: on 42
clips the median per-clip maximum is 0.015, ordinary motion stays below 0.18, and a real internal cut scored 0.53;
CUT_THRESHOLD separates them.
"""
import re
import subprocess
from typing import List, Optional, Tuple

CUT_THRESHOLD = 0.35


def cuts(path: str) -> Tuple[List[float], float]:
    """(times in seconds of internal hard cuts, clip fps)"""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-vf",
                        "select='gte(scene,0)',metadata=print:key=lavfi.scene_score", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = re.search(r"(\d+(?:\.\d+)?) fps", r)
    fps = float(m.group(1)) if m else 24.0
    sc = [float(x) for x in re.findall(r"lavfi.scene_score=([\d.]+)", r)]
    return [i / fps for i, x in enumerate(sc) if i > 0 and x > CUT_THRESHOLD], fps


def longest_clean_span(path: str, duration: float, min_keep: float = 0.7) -> Optional[Tuple[float, float]]:
    """The longest cut-free (t0, t1) if it keeps >= min_keep of the clip, else None (regenerate instead)."""
    ts, fps = cuts(path)
    if not ts:
        return (0.0, duration)
    edges = [0.0] + ts + [duration]
    spans = [(a + 1.0 / fps, b - 1.0 / fps) if a > 0 else (a, b - 1.0 / fps) for a, b in zip(edges, edges[1:])]
    t0, t1 = max(spans, key=lambda s: s[1] - s[0])
    return (t0, t1) if (t1 - t0) >= min_keep * duration else None
