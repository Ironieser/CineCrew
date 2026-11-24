#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
composite: deterministic insertion of an exact prop into a generated frame. A prop rendered by code (a planet with a
dark night side) is exact; image / video models redraw it from their prior. A VLM gives a rough box; the body is then
located exactly here (the largest bright blob against a dark sky, fitted as a disc), checked to be unobstructed (a
ring of sky around it) and the sprite (RGBA cut-out) is pasted over it. Round bodies only (planets, moons, a sun).
"""
from collections import deque
from typing import Optional, Sequence, Tuple

import numpy as np
from PIL import Image

SKY = 30          # luminance below this is sky (stars are small and ignored)
BODY = 45         # luminance above this is a lit part of the body


def _components(mask: np.ndarray):
    """4-connected components of a boolean mask (small images only): yields (n_pixels, ys, xs)."""
    seen = np.zeros_like(mask, bool)
    H, W = mask.shape
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        q, ys, xs = deque([(y0, x0)]), [], []
        seen[y0, x0] = True
        while q:
            y, x = q.popleft()
            ys.append(y); xs.append(x)
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v, u = y + dy, x + dx
                if 0 <= v < H and 0 <= u < W and mask[v, u] and not seen[v, u]:
                    seen[v, u] = True
                    q.append((v, u))
        yield len(ys), np.array(ys), np.array(xs)


def locate_disc(image_path: str, box: Sequence[float], pad: float = 0.35) -> Optional[Tuple[float, float, float]]:
    """Exact disc (cx, cy, r in pixels) of a round body near `box` ([x0, y0, x1, y1], 0-1000, a VLM's rough box), or
    None when it cannot be fitted or something other than sky surrounds it (a window frame, a person: obstructed)."""
    im = Image.open(image_path).convert("L")
    W, H = im.size
    x0, y0, x1, y1 = [float(v) / 1000.0 for v in box]
    bw, bh = (x1 - x0) * W, (y1 - y0) * H
    X0, Y0 = int(max(0, x0 * W - pad * bw)), int(max(0, y0 * H - pad * bh))
    X1, Y1 = int(min(W, x1 * W + pad * bw)), int(min(H, y1 * H + pad * bh))
    if X1 - X0 < 8 or Y1 - Y0 < 8:
        return None
    k = max(1.0, max(X1 - X0, Y1 - Y0) / 240.0)               # work on <= 240 px for the flood fill
    sub = im.crop((X0, Y0, X1, Y1)).resize((max(1, int((X1 - X0) / k)), max(1, int((Y1 - Y0) / k))))
    L = np.asarray(sub, dtype=np.float32)
    best = max(_components(L > BODY), key=lambda c: c[0], default=None)
    if best is None or best[0] < 30:
        return None
    _, ys, xs = best
    bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    w, h = bx1 - bx0, by1 - by0
    if by0 == 0 or bx0 == 0 or by1 >= L.shape[0] or bx1 >= L.shape[1]:
        return None                                             # touches the search window: a horizon, not a disc
    if w >= 0.85 * h and h >= 0.85 * w:                         # whole lit disc
        cx, cy, r = (bx0 + bx1) / 2, (by0 + by1) / 2, (w + h) / 4
    elif w < h:                                                 # lit half / gibbous, terminator vertical
        r = h / 2
        cols = np.bincount(xs - bx0, minlength=w)
        # the longest column is on the terminator side; the curved limb, r from the centre, is the far side
        cx = bx0 + r if np.argmax(cols) >= w / 2 else bx1 - r
        cy = (by0 + by1) / 2
    else:
        return None
    if np.pi * r * r * 0.35 > best[0]:                           # too little of the disc is lit to trust the fit
        return None
    yy, xx = np.mgrid[0:L.shape[0], 0:L.shape[1]]
    d = np.hypot(xx - cx, yy - cy)
    ring = (d > 1.12 * r) & (d < 1.35 * r)
    inside = (d < 0.98 * r)
    if ring.sum() < 20 or (L[ring] < SKY).mean() < 0.9:
        return None                                             # not surrounded by sky: obstructed or framed
    dark_half = inside & (L < SKY)
    lit = inside & (L > BODY)
    if (dark_half.sum() + lit.sum()) < 0.8 * inside.sum():
        return None                                             # something else inside the disc
    return X0 + cx * k, Y0 + cy * k, r * k


def paste_disc(image_path: str, sprite_path: str, disc: Tuple[float, float, float], out_path: str = None,
               cover: float = 1.04) -> str:
    """Paste a round sprite (RGBA, cropped to its alpha) centred on `disc` = (cx, cy, r) px, diameter 2r x `cover`.
    In place unless `out_path` is given. Returns the written path."""
    im = Image.open(image_path).convert("RGB")
    sp = Image.open(sprite_path).convert("RGBA")
    bbox = sp.getchannel("A").getbbox()
    if bbox:
        sp = sp.crop(bbox)
    cx, cy, r = disc
    D = max(2, round(2 * r * cover))
    sp = sp.resize((D, D), Image.LANCZOS)
    im.paste(sp, (round(cx - D / 2), round(cy - D / 2)), sp)
    out = out_path or image_path
    im.save(out)
    return str(out)
