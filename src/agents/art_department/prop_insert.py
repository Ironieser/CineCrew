#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
World props: props the film's world facts name (a planet seen through a window) that have a reference picture.
`insert_props` finds each prop that has a sprite in a frame (prop_locate.yaml: rough box), fits it exactly and pastes
the exact prop over the generated one when sky surrounds it (src/skills/composite.py). Image and video models redraw
such props from their prior (a planet's dark night side comes out lit); the code render is exact. Used on location
plates (ArtDepartment) and keyframes (ProductionOperator).
"""
import logging
import re
from pathlib import Path
from typing import List

from ...engine import ConfigurableAgent
from ...schemas.assets import AssetLibrary
from ...skills.composite import locate_disc, paste_disc

logger = logging.getLogger(__name__)
_HERE = Path(__file__).resolve().parent


def world_props(library: AssetLibrary, facts: List[str], staged_ids=None) -> list:
    """Props with an existing reference picture whose name the world facts mention (critical first, at most 2).
    `staged_ids` restricts them to props staged in a given set of shots (a location's)."""
    text = " ".join(facts or []).lower()
    out = []
    for p in library.props:
        img = p.visual_references.canonical_image_path if p.visual_references else None
        words = re.findall(r"[a-z]{4,}", (p.name or "").lower())
        if staged_ids is not None and p.id not in staged_ids:
            continue
        if img and Path(img).exists() and any(w in text for w in words):
            out.append(p)
    out.sort(key=lambda p: {"critical": 0, "supporting": 1}.get(p.importance, 2))
    return out[:2]


def insert_props(image: str, props) -> List[str]:
    """Paste the exact sprite of every given prop that is visible and unobstructed in `image` (in place). Returns
    the names of the props pasted."""
    agent = None
    done = []
    for p in props:
        sprite = p.visual_references.sprite_path if p.visual_references else None
        if not (sprite and Path(sprite).exists()):
            continue
        agent = agent or ConfigurableAgent(config_path=str(_HERE / "prop_locate.yaml"))
        try:
            r = agent.run(images=[image, p.visual_references.canonical_image_path], prop=p.name)
            disc = locate_disc(image, r.box) if (r.present and len(r.box) == 4) else None
        except Exception as e:
            logger.warning("PropLocate failed for %s (%s)", p.id, e)
            continue
        if disc is None:
            continue
        paste_disc(image, sprite, disc)
        done.append(p.name)
        print(f"      🧩 pasted the exact {p.name} (centre {disc[0]:.0f},{disc[1]:.0f}, r {disc[2]:.0f} px)", flush=True)
    return done
