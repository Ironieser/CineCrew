#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
remake_asset: asset-level repair. Re-render a character's reference sheet with a correction note (what QA found wrong,
e.g. "looks like a toddler, must be a 16-year-old teenager"), in place, so every shot conditioned on it picks up the
new identity. The old sheet is kept as <name>.bad<N>.png; the character's cast voice is dropped so it is re-cast
from the new sheet (a voice cast on a wrong identity is wrong too).

  python tools/remake_asset.py <run_dir> --char char_xiao_yu --note "..."
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.art_department import ArtDepartmentAgent  # noqa: E402
from src.adapters.t2i_client import split_negative  # noqa: E402
from src.schemas.assets import AssetLibrary  # noqa: E402


def remake(run: Path, char_id: str, note: str) -> Path:
    lib_p = run / "assets" / "asset_library.json"
    lib = AssetLibrary.model_validate_json(lib_p.read_text())
    ch = lib.get_character_by_id(char_id)
    if ch is None or not (ch.visual_references and ch.visual_references.canonical_image_path):
        raise SystemExit(f"[remake] {char_id}: no reference sheet to remake")
    img = Path(ch.visual_references.canonical_image_path)
    img = img if img.is_absolute() else ROOT / img
    n = len(list(img.parent.glob(f"{img.stem}.bad*.png"))) + 1
    shutil.copy(img, img.with_name(f"{img.stem}.bad{n}.png"))
    for v in (img.with_name(img.stem + ".voice.wav"), img.with_name(img.stem + ".voice.txt")):
        v.unlink(missing_ok=True)
    art = ArtDepartmentAgent()
    try:
        prompt = art._character_prompter().run(ch.model_dump(), lib.global_style)
    except Exception:
        prompt = ch.description or ch.name
    prompt = f"{prompt}\n\nCORRECTION (the previous sheet was wrong): {note}"
    tmp = img.with_name(f"{img.stem}.new.png")
    if not art._render_reference(ch, prompt, tmp, split_negative):
        shutil.copy(img.with_name(f"{img.stem}.bad{n}.png"), img)
        raise SystemExit(f"[remake] {char_id}: rendering failed; kept the old sheet")
    shutil.move(tmp, img)
    ch.visual_references.canonical_image_path = str(img.relative_to(ROOT)) if str(img).startswith(str(ROOT)) else str(img)
    ch.visual_references.generation_prompt = prompt
    lib_p.write_text(lib.model_dump_json(indent=2))
    print(f"[remake] {char_id}: new sheet {img.name} (old kept as {img.stem}.bad{n}.png; voice will be re-cast)", flush=True)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir"); ap.add_argument("--char", required=True); ap.add_argument("--note", required=True)
    a = ap.parse_args()
    remake(Path(a.run_dir), a.char, a.note)


if __name__ == "__main__":
    main()
