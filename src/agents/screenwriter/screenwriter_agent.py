#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
ScreenwriterAgent — source material -> filmable short script (screenwriter.yaml) -> our_dataset/<Story>/
script_synopsis.json. Checked deterministically after writing: quoted lines exist, line count fits the length, every
listed character is named in the script; one revision round with the problems as feedback.
"""
import json
import re
from pathlib import Path
from typing import List

from ...engine import ConfigurableAgent
from ...schemas.screenplay import Screenplay
from ...skills.script_coverage import script_lines

_HERE = Path(__file__).resolve().parent


class ScreenwriterAgent:
    def __init__(self):
        self._agent = ConfigurableAgent(config_path=str(_HERE / "screenwriter.yaml"))

    def write(self, source: str, kind: str = "novel excerpt", seconds: int = 60, language: str = "Chinese",
              max_characters: int = 3, max_locations: int = 2, lines_per_minute: int = 6) -> Screenplay:
        kw = dict(seconds=seconds, language=language, max_characters=max_characters, max_locations=max_locations,
                  lines_per_minute=lines_per_minute, kind=kind)
        sp = self._agent.run(source=source[:20000], **kw)
        problems = self.problems(sp, seconds, lines_per_minute, max_characters)
        if problems:
            print(f"   ✏️  [Screenwriter] revising: {problems}", flush=True)
            sp2 = self._agent.run(source=source[:20000] + "\n\nREVISE the previous draft; it had these problems: "
                                  + "; ".join(problems), **kw)
            if len(self.problems(sp2, seconds, lines_per_minute, max_characters)) < len(problems):
                sp = sp2
        return sp

    @staticmethod
    def problems(sp: Screenplay, seconds: int, lpm: int, max_chars: int) -> List[str]:
        out, lines = [], script_lines(sp.script)
        want = max(1, round(lpm * seconds / 60))
        if not lines:
            out.append("no quoted dialogue")
        elif len(lines) > want * 1.6:
            out.append(f"{len(lines)} lines is too many for {seconds}s (about {want})")
        if len(sp.characters) > max_chars:
            out.append(f"{len(sp.characters)} characters (max {max_chars})")
        for c in sp.characters:   # "Lin Zhou (林舟)" or "林舟 (Lin Zhou)": either name in the script is enough
            parts = [p.strip() for p in re.split(r"[（()）]", c) if p.strip()]
            if parts and not any(p in sp.script for p in parts):
                out.append(f"character {c} is not named in the script")
        long = [l for l in lines if len(re.sub(r"\W", "", l)) > 24]
        if long:
            out.append(f"{len(long)} line(s) too long to speak in one shot")
        return out

    @staticmethod
    def save(sp: Screenplay, dataset_root: Path) -> Path:
        name = re.sub(r"[^A-Za-z0-9]", "", (sp.title_en or "Story").title()) or "Story"
        d = Path(dataset_root) / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "script_synopsis.json").write_text(json.dumps(
            {"MovieScript": sp.script, "Character": sp.characters, "Title": sp.title, "Logline": sp.logline,
             "AdaptationNotes": sp.adaptation_notes}, ensure_ascii=False, indent=1))
        return d
