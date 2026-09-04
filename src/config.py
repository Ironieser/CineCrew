#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Runtime configuration — everything comes from environment variables.

No secrets live in this file. Put your keys in a `.env` at the project root
(gitignored; see `.env.example`) or export them in your shell.

All three model backends speak the OpenAI API shape, so any OpenAI-compatible
server (OpenAI, Azure OpenAI, vLLM, Ollama, LiteLLM, a self-hosted T2V wrapper,
...) can be plugged in by pointing `*_BASE_URL` / `*_API_KEY` / `*_MODEL` at it:

    LLM    -> POST {LLM_BASE_URL}/chat/completions   (structured JSON via `instructor`; vision for the judge)
    T2I    -> POST {T2I_BASE_URL}/images/generations  (+ /images/edits for reference-conditioned keyframes)
    Video  -> POST {VIDEO_BASE_URL}/videos            (+ GET /videos/{id}, /videos/{id}/content)

Defaults for T2I / Video are the self-hosted models used in the paper (Qwen-Image on
:8000, Wan 2.2 on :8090) behind OpenAI-compatible servers; their API keys fall back
to the LLM key.
"""

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path = _PROJECT_ROOT / ".env") -> None:
    """Minimal .env loader (KEY=VALUE, `#` comments, optional quotes). Real env vars win."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_dotenv()


def _env(*names: str, default: str = "") -> str:
    """First non-empty value among several env var names (lets legacy names keep working)."""
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return default


class Config:
    # ── LLM (the crew's brain) ───────────────────────────────────────────────
    # LLM_PROVIDER: "openai" (default; any OpenAI-compatible endpoint) or "azure".
    LLM_PROVIDER = _env("LLM_PROVIDER", default="openai").lower()
    LLM_API_KEY = _env("LLM_API_KEY", "OPENAI_API_KEY")
    # None -> the openai SDK default (https://api.openai.com/v1).
    LLM_BASE_URL = _env("LLM_BASE_URL", "OPENAI_BASE_URL", "AZURE_ENDPOINT") or None
    # For Azure this must be the *deployment name*.
    LLM_MODEL = _env("LLM_MODEL", "AZURE_DEPLOYMENT_NAME", "MODEL_NAME", default="gpt-5")
    AZURE_API_VERSION = _env("AZURE_API_VERSION", default="2024-10-21")

    # Retries on invalid JSON / schema violations (instructor) and on connection errors /
    # timeouts (openai client). 0 = fail-fast for debugging.
    LLM_MAX_RETRIES = int(_env("LLM_MAX_RETRIES", "MAX_RETRIES", default="2"))
    # Per-request timeout in seconds (long structured outputs can take minutes).
    LLM_TIMEOUT = float(_env("LLM_TIMEOUT", default="600"))
    # Max tokens per completion (incl. reasoning). Too small -> truncated JSON.
    LLM_MAX_COMPLETION_TOKENS = int(_env("LLM_MAX_COMPLETION_TOKENS", "MAX_COMPLETION_TOKENS", default="32768"))

    # ── T2I (keyframes / character reference sheets) ─────────────────────────
    T2I_MODEL = _env("T2I_MODEL", default="qwen-image")
    T2I_BASE_URL = _env("T2I_BASE_URL", "T2I_ENDPOINT", default="http://localhost:8000/v1")
    T2I_API_KEY = _env("T2I_API_KEY") or LLM_API_KEY or "EMPTY"
    T2I_SIZE = _env("T2I_SIZE", default="1024x1024")               # reference sheets
    T2I_KEYFRAME_SIZE = _env("T2I_KEYFRAME_SIZE") or _env("VIDEO_SIZE", default="1280x720")  # shot keyframes = video frame

    # ── Video (T2V / I2V execution of the FilmDSL jobs) ──────────────────────
    VIDEO_MODEL = _env("VIDEO_MODEL", default="wan22-t2v")  # wan22-t2v | wan22-i2v
    VIDEO_BASE_URL = _env("VIDEO_BASE_URL", "VIDEO_ENDPOINT", default="http://localhost:8090/v1")
    VIDEO_API_KEY = _env("VIDEO_API_KEY") or LLM_API_KEY or "EMPTY"
    VIDEO_SIZE = _env("VIDEO_SIZE", default="1280x720")
    VIDEO_FPS = int(_env("VIDEO_FPS", default="16"))
    VIDEO_POLL_INTERVAL = float(_env("VIDEO_POLL_INTERVAL", default="5"))
    VIDEO_TIMEOUT = float(_env("VIDEO_TIMEOUT", default="1800"))

    # ── Legacy attribute names (kept so older code / traces keep working) ─────
    USE_AZURE = LLM_PROVIDER == "azure"
    OPENAI_API_KEY = LLM_API_KEY
    AZURE_ENDPOINT = LLM_BASE_URL
    MODEL_NAME = LLM_MODEL
    API_VERSION = AZURE_API_VERSION
    MAX_RETRIES = LLM_MAX_RETRIES
    MAX_COMPLETION_TOKENS = LLM_MAX_COMPLETION_TOKENS
