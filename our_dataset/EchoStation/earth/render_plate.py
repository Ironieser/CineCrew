#!/usr/bin/env python3
"""Prop reference for 'Earth Viewport': Earth as seen from the Moon's near side, physically lit (NASA Blue Marble
texture, public domain), half day / half night, the night hemisphere completely dark (no city lights - the story's
twist), black sky with faint stars. Used as a keyframe reference picture (prop_list/EarthViewport/best.png)."""
import numpy as np
from pathlib import Path
from PIL import Image

HERE = Path(__file__).parent
W, H = 1344, 768
TEX = np.asarray(Image.open(HERE / "earth_tex.jpg").convert("RGB")).astype(np.float32) / 255.0
TH, TW = TEX.shape[:2]
rng = np.random.default_rng(7)
cx, cy, R = W // 2, H // 2, 300
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
x = (xx - cx) / R; y = -(yy - cy) / R; r2 = x * x + y * y; disk = r2 <= 1
z = np.sqrt(np.clip(1 - r2, 0, 1))
lat0, lon0 = np.radians(10), np.radians(15)
lat = np.arcsin(np.clip(y * np.cos(lat0) + z * np.sin(lat0), -1, 1))
lon = lon0 + np.arctan2(x, z * np.cos(lat0) - y * np.sin(lat0))
u = ((lon / (2 * np.pi) + 0.5) % 1) * (TW - 1); v = (0.5 - lat / np.pi) * (TH - 1)
col = TEX[v.astype(int).clip(0, TH - 1), u.astype(int).clip(0, TW - 1)]
sun = np.array([-0.95, 0.15, 0.25]); sun /= np.linalg.norm(sun)          # light from the left: terminator near the middle
ndl = x * sun[0] + y * sun[1] + z * sun[2]
lit = col * ((0.03 + 0.97 * np.clip(ndl, 0, 1) ** 0.8) * np.clip((ndl + 0.03) / 0.10, 0, 1))[..., None]
rim = np.clip(1 - z, 0, 1) ** 3 * np.clip(ndl + 0.2, 0, 1)
lit += rim[..., None] * np.array([0.25, 0.45, 0.95])
img = np.zeros((H, W, 3), np.float32)
stars = rng.random((H, W)) > 0.9988
img[stars] = rng.uniform(0.25, 0.8, (stars.sum(), 1))
img[disk] = lit[disk]
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(HERE.parent / "prop_list" / "EarthViewport" / "best.png")
print("wrote prop_list/EarthViewport/best.png")
