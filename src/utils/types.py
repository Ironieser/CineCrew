#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Common types: the Envelope Pattern.

LLMResult[T] bundles business data (T) with metadata (Usage / Metadata) for return, using explicit types and avoiding monkey patching.
"""

from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass
class TokenUsage:
    """Unified token accounting structure (billing and monitoring)."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cache_hit_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cache_hit_tokens": self.cache_hit_tokens,
        }


@dataclass
class LLMResult(Generic[T]):
    """
    The "envelope" for an LLM response.
    - content: business data (AssetLibrary, CinematicDSL, etc.)
    - usage: consumption data (billing)
    - latency: elapsed time (seconds)
    - raw_response: the raw API response (optional, for debugging)
    """
    content: T
    usage: TokenUsage
    latency: float = 0.0
    raw_response: Optional[Any] = None
