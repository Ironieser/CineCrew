#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
T2IClient: OpenAI-style image generation adapter.

    POST {base_url}/images/generations   render(prompt)                        T2I
    POST {base_url}/images/edits         render(prompt, reference_images=[..]) TI2I ("Picture N" = n-th reference)

Used for character reference sheets and location establishing shots (Art
Department) and for shot keyframes (Production Operator). Non-OpenAI knobs
(negative_prompt, seed, steps, cfg, ...) travel in `extra_body`, so a self-hosted
Qwen-Image / FLUX / SD server behind an OpenAI-compatible route can use them and
OpenAI ignores them. Pure adapter: no prompt engineering here.
"""

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import Config


class T2IClient:
    """
    Usage:
        client = T2IClient()                                        # T2I_* from Config / .env
        client = T2IClient(model="qwen-image", base_url="http://localhost:8000/v1")
        png = client.render("a cinematic portrait ...", negative_prompt="blurry")
        client.render_to_file(Path("kf.png"), prompt=..., reference_images=["saul.png"])
    """

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        from openai import OpenAI

        self.model = model or Config.T2I_MODEL
        self.base_url = base_url or Config.T2I_BASE_URL
        self._client = OpenAI(api_key=api_key or Config.T2I_API_KEY or "EMPTY", base_url=self.base_url)
        print(f"   T2IClient initialized: model={self.model}, base_url={self.base_url or '<openai default>'}")

    def render(
        self,
        prompt: str,
        negative_prompt: str = "",
        reference_images: Optional[List[str]] = None,
        size: Optional[str] = None,
        seed: Optional[int] = None,
        model: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """One image as PNG bytes. With `reference_images` the call goes to /images/edits (TI2I)."""
        extra_body: Dict[str, Any] = {"negative_prompt": negative_prompt}
        if seed is not None:
            extra_body["seed"] = seed
        extra_body.update(extra or {})
        kwargs: Dict[str, Any] = dict(
            model=model or self.model,
            prompt=prompt,
            n=1,
            size=size or Config.T2I_SIZE,
            extra_body=extra_body,
        )
        if reference_images:
            handles = [open(p, "rb") for p in reference_images]
            try:
                response = self._client.images.edit(image=handles, **kwargs)
            finally:
                for h in handles:
                    h.close()
        else:
            response = self._client.images.generate(**kwargs)
        return _decode_image(response)

    def render_to_file(self, out_path: Path, **kwargs) -> Path:
        """render() and write the PNG to `out_path`."""
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(self.render(**kwargs))
        return out_path


def _decode_image(response) -> bytes:
    """Images API responses carry either b64_json or a url."""
    image = response.data[0]
    if getattr(image, "b64_json", None):
        return base64.b64decode(image.b64_json)
    if getattr(image, "url", None):
        import urllib.request

        with urllib.request.urlopen(image.url, timeout=120) as r:
            return r.read()
    raise ValueError("Images API returned neither b64_json nor url")


def split_negative(prompt: str) -> tuple:
    """Split a template prompt of the form '<positive>\\n\\nNegative: <negative>'."""
    parts = prompt.split("\n\nNegative:")
    return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")
