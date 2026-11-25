#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
outage: ride out a backend that is briefly unreachable (a VPN / tunnel drop, a replica restarting) instead of
failing every job that runs into it. A run that hit a 1-hour drop otherwise marks every shot of that hour failed and
spends its repair rounds re-rendering them.
"""
import time

from ..config import Config

_MARKERS = ("APIConnectionError", "APITimeoutError", "Connection error", "Connection refused", "ConnectionRefused",
            "ConnectionReset", "RemoteDisconnected", "Broken pipe", "BrokenPipe", "Name or service not known",
            "timed out", "502 Bad Gateway", "503 Service")


def is_outage(e: BaseException) -> bool:
    """Network-level failure (not a bad request or a failed generation)."""
    s = f"{type(e).__name__}: {e}"
    return any(m in s for m in _MARKERS)


def with_outage_retry(fn, what: str, budget: float = None):
    """Call fn(); while it fails with an outage, wait (15 s doubling to 2 min) and retry, up to `budget` seconds
    (BACKEND_OUTAGE_WAIT, default 30 min). Any other error, or the budget spent, re-raises."""
    budget = Config.BACKEND_OUTAGE_WAIT if budget is None else budget
    t0, delay = time.monotonic(), 15.0
    while True:
        try:
            return fn()
        except Exception as e:
            if not is_outage(e) or time.monotonic() - t0 + delay > budget:
                raise
            print(f"      ⏳ {what}: backend unreachable ({type(e).__name__}); retrying in {delay:.0f}s", flush=True)
            time.sleep(delay)
            delay = min(delay * 2, 120.0)
