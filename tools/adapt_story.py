#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
adapt_story: source material -> our_dataset/<Story>/script_synopsis.json (ScreenwriterAgent), ready for produce.py.

  python tools/adapt_story.py <source.txt> --kind "novel excerpt" --seconds 60 [--out our_dataset]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.screenwriter import ScreenwriterAgent  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source"); ap.add_argument("--kind", default="novel excerpt")
    ap.add_argument("--seconds", type=int, default=60); ap.add_argument("--out", default=str(ROOT / "our_dataset"))
    ap.add_argument("--max-characters", type=int, default=3)
    a = ap.parse_args()
    sp = ScreenwriterAgent().write(Path(a.source).read_text(), kind=a.kind, seconds=a.seconds,
                                   max_characters=a.max_characters)
    d = ScreenwriterAgent.save(sp, Path(a.out))
    print(f"[adapt] {sp.title} ({sp.title_en}) -> {d}\n  characters: {sp.characters}\n  notes: {sp.adaptation_notes[:300]}")
    print(sp.script)


if __name__ == "__main__":
    main()
