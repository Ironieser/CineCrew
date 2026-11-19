#!/usr/bin/env python3
"""Code-rendered keyframes for the ending shot (mixed modality): physically lit Earth seen from the Moon's near side,
night hemisphere completely dark (no city lights — the story's twist), through a porthole with Lin Zhou's silhouette.
Texture: NASA Blue Marble "Land shallow topo" (Reto Stöckli / NASA GSFC, public domain).
Writes first.png (t=0) and last.png (t=end) at 1344x768 for H3 FL2VA first/last-frame conditioning."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

HERE = Path(__file__).parent
W, H = 1344, 768
TEX = np.asarray(Image.open(HERE / "earth_tex.jpg").convert("RGB")).astype(np.float32) / 255.0
TH, TW = TEX.shape[:2]
rng = np.random.default_rng(42)

def fractal_noise(h, w, octaves=6):
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        s = 2 ** (o + 4)
        n = rng.random((s, s * 2)).astype(np.float32)
        n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
        out += amp * n; tot += amp; amp *= 0.5
    return out / tot

CLOUD = fractal_noise(TH // 2, TW // 2)
CLOUD = np.asarray(Image.fromarray((np.clip((CLOUD - 0.56) * 3.0, 0, 1) ** 1.4 * 255).astype(np.uint8)).resize((TW, TH), Image.BICUBIC)).astype(np.float32) / 255

def render(cx, cy, R, lon0_deg, lat0_deg, sun_phase_deg, out, porthole_scale, silhouette_shift):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x = (xx - cx) / R; y = -(yy - cy) / R; r2 = x * x + y * y
    disk = r2 <= 1.0
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    lat0, lon0 = np.radians(lat0_deg), np.radians(lon0_deg)
    lat = np.arcsin(np.clip(y * np.cos(lat0) + z * np.sin(lat0), -1, 1))
    lon = lon0 + np.arctan2(x, z * np.cos(lat0) - y * np.sin(lat0))
    u = ((lon / (2 * np.pi) + 0.5) % 1.0) * (TW - 1); v = (0.5 - lat / np.pi) * (TH - 1)
    col = TEX[v.astype(int).clip(0, TH - 1), u.astype(int).clip(0, TW - 1)]
    cl = CLOUD[v.astype(int).clip(0, TH - 1), u.astype(int).clip(0, TW - 1)][..., None]
    col = col * (1 - 0.7 * cl) + 0.85 * cl
    ph = np.radians(sun_phase_deg)
    sun = np.array([-np.sin(ph), 0.12, np.cos(ph)]); sun /= np.linalg.norm(sun)       # sun from the left
    ndl = x * sun[0] + y * sun[1] + z * sun[2]
    light = np.clip(ndl, 0, 1) ** 0.8
    term = np.clip((ndl + 0.04) / 0.12, 0, 1)                                          # soft terminator
    lit = col * ((0.02 + 0.98 * light) * term)[..., None]                                          # night side -> black
    rim = np.clip(1 - z, 0, 1) ** 3 * np.clip(ndl + 0.2, 0, 1)                         # atmosphere on lit limb
    lit += rim[..., None] * np.array([0.25, 0.45, 0.95])
    img = np.zeros((H, W, 3), np.float32)
    stars = rng.random((H, W)) > 0.9985
    img[stars] = rng.uniform(0.3, 0.9, (stars.sum(), 1))
    halo_r = np.sqrt(r2)
    halo = np.clip(1 - (halo_r - 1) / 0.06, 0, 1) * (halo_r > 1) * np.clip((x * sun[0] + y * sun[1]) / np.maximum(halo_r, 1e-3) + 0.3, 0, 1)
    img += halo[..., None] * np.array([0.12, 0.25, 0.6])
    img[disk] = lit[disk]
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    # porthole: dark interior wall with a rounded window opening
    wall = Image.new("RGBA", (W, H), (22, 24, 28, 255)); d = ImageDraw.Draw(wall)
    pw, phh = int(1180 * porthole_scale), int(700 * porthole_scale)
    box = [W // 2 - pw // 2 + 40, H // 2 - phh // 2, W // 2 + pw // 2 + 40, H // 2 + phh // 2]
    d.rounded_rectangle(box, radius=int(160 * porthole_scale), fill=(0, 0, 0, 0))
    d.rounded_rectangle([box[0] - 18, box[1] - 18, box[2] + 18, box[3] + 18], radius=int(175 * porthole_scale), outline=(58, 60, 66, 255), width=14)
    im = Image.alpha_composite(im.convert("RGBA"), wall)
    # foreground silhouette: back of Lin Zhou's head and shoulder, backlit (very dark, soft)
    sil = Image.new("RGBA", (W, H), (0, 0, 0, 0)); s = ImageDraw.Draw(sil)
    ox = silhouette_shift
    s.ellipse([ox + 20, 330, ox + 330, 700], fill=(6, 6, 8, 255))                         # head
    s.rectangle([ox - 140, 640, ox + 520, 800], fill=(6, 6, 8, 255))                    # shoulders
    s.ellipse([ox - 220, 560, ox + 560, 1000], fill=(6, 6, 8, 255))
    sil = sil.filter(ImageFilter.GaussianBlur(6))
    im = Image.alpha_composite(im, sil).convert("RGB")
    im.save(HERE / out); print("wrote", out)

# t=0: Africa/Europe near centre, terminator on the right; t=end: camera pushed in, Earth rotated so Africa
# has moved into the dark hemisphere (time-lapse), night side larger — still not a single light.
render(cx=760, cy=384, R=250, lon0_deg=20, lat0_deg=12, sun_phase_deg=70, out="first.png", porthole_scale=1.0, silhouette_shift=-120)
render(cx=720, cy=384, R=330, lon0_deg=-5, lat0_deg=12, sun_phase_deg=95, out="last.png", porthole_scale=1.32, silhouette_shift=-420)
