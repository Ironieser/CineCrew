#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Script coverage: every quoted line of the script must be spoken in some shot. Planning LLMs compress short scripts
and silently drop lines and the closing beat; a film can then pass every per-shot check while missing its point.
"""
import re
from typing import Iterable, List

# each quote family is matched with its own closing mark, so a nested quote (‘…“锁住”…’) stays inside its line
_QUOTES = re.compile(r"“([^”]{2,200})”|‘([^’]{2,200})’|「([^」]{2,200})」|『([^』]{2,200})』|\"([^\"]{2,200})\"")
_PUNCT = re.compile(r"[\s，。？！、,.?!;；:：…—\-~～'’‘]")


def norm(s: str) -> str:
    return _PUNCT.sub("", s or "").lower()


def script_lines(script: str) -> List[str]:
    """Quoted spoken lines, in order (straight or CJK quotes)."""
    out = []
    for m in _QUOTES.finditer(script or ""):
        g = next(x for x in m.groups() if x is not None).strip()
        if norm(g):
            out.append(g)
    return out


def missing_lines(script: str, spoken: Iterable[str]) -> List[str]:
    """Script lines that no planned line contains (punctuation-insensitive; a line split over shots still counts)."""
    said = norm("".join(spoken))
    return [l for l in script_lines(script) if norm(l) not in said]


# narration followed by speech: '从布袋里拿出一枚硬币，……："下次早点来还。"'
_NARRATED = re.compile(r"[：:]\s*[“\"「『‘]")


def spoken_only(text: str) -> str:
    """The words actually said. Planners sometimes copy a script sentence with its narration into the dialogue
    ('…把袋子挂回豆豆的脖子上：“下次早点来还。”'): the video model would voice the stage directions and the clip
    length (derived from the line) balloons. Narration-then-quote text keeps only the quoted speech."""
    if not text or not _NARRATED.search(text):
        return text
    qs = [next(x for x in m.groups() if x is not None).strip() for m in _QUOTES.finditer(text)]
    return " ".join(q for q in qs if norm(q)) or text

