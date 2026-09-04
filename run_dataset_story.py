#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
run_dataset_story.py — entry point: one story in, a FilmDSL plan (+ optionally the film) out.

Usage:
  python run_dataset_story.py our_dataset/BetterCallSaul2
  python run_dataset_story.py our_dataset/CineMoments/script_snippets.json --moment great_gatsby_fireworks_smile
  python run_dataset_story.py our_dataset/CineMoments/script_snippets.json --all-moments
  python run_dataset_story.py our_dataset/BetterCallSaul2 --skip dailies_reviewer      # any stage id
  python run_dataset_story.py our_dataset/BetterCallSaul2 --execute                    # render + judge + stitch

Inputs:
  <story_dir>/script_synopsis.json        { "MovieScript": "...", "Character": ["Saul", "Judge"] }
  <story_dir>/character_list/<Name>/best.png   optional reference image per character
  <file>.json with {"moments": [{"id", "title", "text", ...}]}   a collection of short scenes

Output:
  data/runs/dataset/<story_name>/<run_id>/
    assets/                 AssetLibrary JSON
    shots/
      scene_blueprint_final.json   complete four-layer Blueprint (all layers filled)
      scene_blueprint_render_filled.json  (intermediate state: render filled)
      video_jobs.json              VideoJobBatch (executable T2V/I2V job specs)
      validation_report.json, dailies_report.json
    media/                  keyframes/, clips/, film.mp4   (only with production_operator.execute: true)
    logs/                   Agent trace logs
"""

import argparse
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# Working directory setup
_PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.pipeline import run_pipeline, get_enabled_stages, load_pipeline_config
from src.schemas.blueprint import SceneBlueprint


# ─────────────────────────────────────────────────────────────────────────────
# Utility functions
# ─────────────────────────────────────────────────────────────────────────────

def load_moment(collection: Path, moment_id: str) -> tuple[str, str]:
    """Return (story_name, script_text) for one entry of a {"moments": [...]} collection."""
    with open(collection, encoding="utf-8") as f:
        moments = json.load(f).get("moments", [])
    for m in moments:
        if m.get("id") == moment_id:
            title = m.get("title", "")
            text = m.get("text", "")
            return moment_id, (f"{title}\n\n{text}" if title else text)
    raise KeyError(f"moment {moment_id!r} not found in {collection} (have: {[m.get('id') for m in moments]})")


def load_story(story_dir: Path) -> tuple[str, list[str], dict[str, Path]]:
    """
    Read script_synopsis.json and the character_list/ directory.

    Returns:
      script_content   : script text
      character_names  : list of character names
      char_images      : { char_name: image_path }
    """
    synopsis_path = story_dir / "script_synopsis.json"
    if not synopsis_path.exists():
        raise FileNotFoundError(f"script_synopsis.json not found in {story_dir}")

    with open(synopsis_path, encoding="utf-8") as f:
        data = json.load(f)

    script_content: str = data.get("MovieScript", "")
    if not script_content:
        raise ValueError("script_synopsis.json: 'MovieScript' field is empty")

    character_names: list[str] = data.get("Character", [])

    # Scan for character images
    char_images: dict[str, Path] = {}
    char_list_dir = story_dir / "character_list"
    if char_list_dir.exists():
        for char_dir in sorted(char_list_dir.iterdir()):
            if not char_dir.is_dir():
                continue
            for img_ext in ["best.png", "best.jpg", "best.jpeg"]:
                img_path = char_dir / img_ext
                if img_path.exists():
                    char_images[char_dir.name] = img_path
                    break

    return script_content, character_names, char_images


def link_character_images(asset_library, char_images: dict[str, Path]) -> None:
    """
    Link the reference images in character_list/ to the
    visual_references.canonical_image_path of the matching character in AssetLibrary.

    Matching rule (case-insensitive, spaces/underscores treated as equivalent):
      char_dir_name ↔ stem of character.name or character.id
    """
    from src.schemas.assets import VisualReferences

    def normalize(s: str) -> str:
        return s.lower().replace("_", "").replace("-", "").replace(" ", "")

    linked = 0
    for char in asset_library.characters:
        for folder_name, img_path in char_images.items():
            if normalize(folder_name) in normalize(char.name) or \
               normalize(char.name) in normalize(folder_name) or \
               normalize(folder_name) in normalize(char.id):
                if char.visual_references is None:
                    char.visual_references = VisualReferences()
                char.visual_references.canonical_image_path = _relative(img_path)
                print(
                    f"   🖼  [{char.id}] linked image: {img_path.name}",
                    flush=True,
                )
                linked += 1
                break

    if linked == 0:
        print(
            "   ⚠️  No character images were auto-linked. "
            "Check character_list/ folder names match character names in script.",
            flush=True,
        )


def _relative(path: Path) -> str:
    """Project-relative path when inside the repo (keeps artifacts portable), else absolute."""
    try:
        return str(Path(path).resolve().relative_to(_PROJECT_ROOT))
    except ValueError:
        return str(path)


def _stage_option(stage_id: str, key: str, default):
    """Read one option of a stage entry in configs/pipeline_settings.yaml."""
    for spec in load_pipeline_config().get("pipeline", {}).get("stages", []) or []:
        if isinstance(spec, dict) and spec.get("id") == stage_id:
            return spec.get(key, default)
    return default


def save_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(obj, "model_dump_json"):
        path.write_text(obj.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"   💾 Saved: {path.relative_to(_PROJECT_ROOT)}", flush=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main flow
# ─────────────────────────────────────────────────────────────────────────────

def run_story(
    story_dir: Optional[Path] = None,
    *,
    story_name: Optional[str] = None,
    script_content: Optional[str] = None,
    skip: tuple = (),
    execute: bool = False,
) -> Path:
    """
    Run the crew on one story. Either `story_dir` (script_synopsis.json + character_list/)
    or `story_name` + `script_content` (a moment from a collection). Returns the run root.
    """
    story_name = story_name or story_dir.name
    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_root = _PROJECT_ROOT / "data" / "runs" / "dataset" / story_name / run_id

    print("=" * 72, flush=True)
    print(f"  Story   : {story_name}", flush=True)
    print(f"  Run     : {run_id}", flush=True)
    print(f"  Output  : {run_root.relative_to(_PROJECT_ROOT)}", flush=True)
    print("=" * 72, flush=True)

    # ── Read input ────────────────────────────────────────────────────────────
    if script_content is None:
        script_content, character_names, char_images = load_story(story_dir)
    else:
        character_names, char_images = [], {}
    print(f"\n📄 Script  : {len(script_content)} chars", flush=True)
    print(f"👥 Characters: {character_names}", flush=True)
    print(f"🖼  Images  : {list(char_images.keys())}", flush=True)

    # One trace for the whole run: Art Department spans below and the pipeline stages
    # share <run_root>/logs and one span sequence.
    from src.utils.agent_trace import new_trace, set_trace_output_dir
    new_trace(session_id=story_name)
    (run_root / "logs").mkdir(parents=True, exist_ok=True)
    set_trace_output_dir(run_root / "logs")

    # ── Stage 1: ArtDepartment (run separately, then add image links) ────────────────────
    print("\n" + "─" * 72, flush=True)
    print("STAGE 1 — ArtDepartment", flush=True)
    print("─" * 72, flush=True)

    from src.agents.art_department import ArtDepartmentAgent
    wb = ArtDepartmentAgent()
    assets_base = str(run_root / "assets")
    asset_library = wb.run(
        script_content,
        enable_hallucination_guard=True,
        base_path=assets_base,
    )

    # Link the pre-supplied character images; render whatever is still missing
    # (characters without an image, location establishing shots) when the
    # art_department stage has `generate_references: true`.
    print("\n🔗 Linking character reference images...", flush=True)
    link_character_images(asset_library, char_images)
    if _stage_option("art_department", "generate_references", False):
        wb.generate_references(asset_library, assets_base)

    # Save AssetLibrary (including image paths)
    save_json(asset_library, run_root / "assets" / "asset_library.json")

    # ── Stage 2–5: Blueprint Pipeline (skip art_department) ───────────────
    print("\n" + "─" * 72, flush=True)
    print("STAGES 2–5 — Blueprint Pipeline", flush=True)
    print("─" * 72, flush=True)

    initial_blueprint = SceneBlueprint.from_asset_library(
        asset_library,
        blueprint_id=f"bp_{story_name.lower()}_{uuid.uuid4().hex[:6]}",
    )

    # Start from the story_editor stage; ArtDepartment already ran above.
    bp_stages = [s for s in get_enabled_stages() if s.get("id") != "art_department" and s.get("id") not in skip]
    if execute:
        bp_stages = [dict(s, execute=True) if s.get("id") == "production_operator" else s for s in bp_stages]
    if skip:
        print(f"   ⏭  skipping stages: {', '.join(skip)}", flush=True)

    bp_ctx = run_pipeline(
        script_content,
        stages=bp_stages,
        session_id=story_name,
        run_root=run_root,
        reuse_trace=True,
        initial_ctx={
            "asset_library": asset_library,
            "scene_blueprint": initial_blueprint,
        },
    )

    # ── Save results ────────────────────────────────────────────────────────────
    shots_dir = run_root / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    blueprint: SceneBlueprint | None = bp_ctx.get("scene_blueprint")
    if blueprint:
        save_json(blueprint, shots_dir / "scene_blueprint_final.json")

    video_jobs = bp_ctx.get("video_jobs")
    if video_jobs:
        save_json(video_jobs, shots_dir / "video_jobs.json")

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 72, flush=True)
    print(f"✅ Done: {story_name}", flush=True)
    if blueprint:
        render_filled = sum(1 for s in blueprint.shots if s.render_layer)
        assembly_set  = sum(1 for s in blueprint.shots if s.assembly_layer)
        print(f"   Blueprint ID  : {blueprint.blueprint_id}", flush=True)
        print(f"   Total shots   : {len(blueprint.shots)}", flush=True)
        print(f"   Render filled : {render_filled}/{len(blueprint.shots)}", flush=True)
        print(f"   Assembly set  : {assembly_set}/{len(blueprint.shots)}", flush=True)
    if video_jobs:
        print(f"   Video jobs    : {video_jobs.total_shots} jobs", flush=True)
    video_results = bp_ctx.get("video_results")
    if video_results:
        done = sum(1 for r in video_results if r.status == "completed")
        print(f"   Clips         : {done}/{len(video_results)} generated", flush=True)
    print(f"\n   Output root: {run_root.relative_to(_PROJECT_ROOT)}", flush=True)
    print("=" * 72, flush=True)
    return run_root


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Run the CineCrew pipeline on one story.")
    ap.add_argument("story", help="story directory (script_synopsis.json) or a moments collection .json")
    ap.add_argument("--moment", help="id of one entry when `story` is a moments collection")
    ap.add_argument("--all-moments", action="store_true", help="run every entry of a moments collection")
    ap.add_argument("--skip", action="append", default=[], metavar="STAGE",
                    help="skip a pipeline stage (e.g. dailies_reviewer); repeatable")
    ap.add_argument("--execute", action="store_true",
                    help="also render keyframes/clips on the T2I_*/VIDEO_* backends and cut the film")
    args = ap.parse_args(argv)

    path = Path(args.story)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    if not path.exists():
        sys.exit(f"Error: not found: {path}")
    skip = tuple(args.skip)

    if path.is_file():
        if args.all_moments:
            with open(path, encoding="utf-8") as f:
                ids = [m["id"] for m in json.load(f).get("moments", [])]
        elif args.moment:
            ids = [args.moment]
        else:
            sys.exit("Error: a moments collection needs --moment <id> or --all-moments")
        for mid in ids:
            name, text = load_moment(path, mid)
            run_story(story_name=name, script_content=text, skip=skip, execute=args.execute)
    else:
        run_story(path, skip=skip, execute=args.execute)


if __name__ == "__main__":
    main()
