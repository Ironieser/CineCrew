#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Asset Management Skill [The Hands]

Pure Python: save / load an AssetLibrary as a folder of JSON files. No LLM.

    <base_path>/
    ├── index.json               project_title, global_style, id lists
    ├── narrative_context.json
    ├── project_settings.json    (when present)
    ├── characters/<id>.json
    ├── locations/<id>.json
    └── props/<id>.json

On save, visual_references / audio_references already on disk are preserved, so
re-running the Art Department never discards reference images or voices you
have already generated.
"""

import json
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel

from ..schemas.assets import (
    AssetLibrary,
    CharacterAsset,
    LocationAsset,
    NarrativeContext,
    PropAsset,
    VisualReferences,
    AudioReferences,
)
from ..schemas.project_settings import ProjectSettings


def _preserve_visual_refs(existing: dict) -> Optional[VisualReferences]:
    """Keep an on-disk VisualReferences if it points at a generated image."""
    vr = existing.get("visual_references")
    if not isinstance(vr, dict) or not (vr.get("canonical_image_path") or vr.get("generation_prompt")):
        return None
    return VisualReferences(**{k: vr[k] for k in vr if k in VisualReferences.model_fields})


def _preserve_audio_refs(existing: dict) -> Optional[AudioReferences]:
    """Keep an on-disk AudioReferences if it points at a generated voice."""
    ar = existing.get("audio_references")
    if not isinstance(ar, dict) or not (ar.get("voice_sample_path") or ar.get("voice_model_id")):
        return None
    return AudioReferences(**{k: ar[k] for k in ar if k in AudioReferences.model_fields})


def _write_preserving(asset: BaseModel, path: Path) -> None:
    if path.exists():
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
            update = {}
            vr = _preserve_visual_refs(old)
            if vr is not None:
                update["visual_references"] = vr
            if "audio_references" in type(asset).model_fields:
                ar = _preserve_audio_refs(old)
                if ar is not None:
                    update["audio_references"] = ar
            if update:
                asset = asset.model_copy(update=update)
        except Exception:
            pass  # unreadable old file: overwrite
    path.write_text(asset.model_dump_json(indent=2), encoding="utf-8")


def save_assets(asset_library: AssetLibrary, base_path: str = "data/output/assets") -> None:
    """Write the library as the folder structure above (preserving generated references)."""
    base = Path(base_path)
    for sub in ("characters", "locations", "props"):
        (base / sub).mkdir(parents=True, exist_ok=True)

    for char in asset_library.characters:
        _write_preserving(char, base / "characters" / f"{char.id}.json")
    for loc in asset_library.locations:
        _write_preserving(loc, base / "locations" / f"{loc.id}.json")
    for prop in asset_library.props:
        _write_preserving(prop, base / "props" / f"{prop.id}.json")

    (base / "narrative_context.json").write_text(
        asset_library.narrative_context.model_dump_json(indent=2), encoding="utf-8"
    )
    index = {
        "project_title": asset_library.project_title,
        "global_style": asset_library.global_style,
        "characters": [c.id for c in asset_library.characters],
        "locations": [l.id for l in asset_library.locations],
        "props": [p.id for p in asset_library.props],
    }
    (base / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    if asset_library.project_settings:
        (base / "project_settings.json").write_text(
            asset_library.project_settings.model_dump_json(indent=2), encoding="utf-8"
        )


def _load_many(base: Path, sub: str, ids: list, model: Type[BaseModel]) -> list:
    out = []
    for asset_id in ids:
        f = base / sub / f"{asset_id}.json"
        if f.exists():
            out.append(model.model_validate_json(f.read_text(encoding="utf-8")))
    return out


def load_asset_library(base_path: str = "data/output/assets") -> Optional[AssetLibrary]:
    """Inverse of save_assets(). Returns None when there is no index.json."""
    base = Path(base_path)
    index_file = base / "index.json"
    if not index_file.exists():
        return None
    index = json.loads(index_file.read_text(encoding="utf-8"))

    ctx_file = base / "narrative_context.json"
    narrative_context = (
        NarrativeContext.model_validate_json(ctx_file.read_text(encoding="utf-8"))
        if ctx_file.exists()
        else NarrativeContext(time_period="Unknown", global_mood="Unknown")
    )
    settings_file = base / "project_settings.json"
    project_settings = (
        ProjectSettings.model_validate_json(settings_file.read_text(encoding="utf-8"))
        if settings_file.exists()
        else None
    )
    return AssetLibrary(
        project_title=index.get("project_title", "Unknown"),
        global_style=index.get("global_style", ""),
        narrative_context=narrative_context,
        project_settings=project_settings,
        characters=_load_many(base, "characters", index.get("characters", []), CharacterAsset),
        locations=_load_many(base, "locations", index.get("locations", []), LocationAsset),
        props=_load_many(base, "props", index.get("props", []), PropAsset),
    )
