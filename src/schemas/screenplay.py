#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""Screenwriter output: a filmable short script + character list (becomes script_synopsis.json)."""
from typing import List

from pydantic import BaseModel, Field


class Screenplay(BaseModel):
    title: str = Field(..., description="Title in the script language")
    title_en: str = Field("", description="English / pinyin title, used for the dataset folder name")
    logline: str = Field("", description="One-sentence summary")
    characters: List[str] = Field(default_factory=list, description='["English or pinyin name (中文名)", ...]')
    script: str = Field(..., description="Prose script with quoted dialogue")
    adaptation_notes: str = Field("", description="What was cut, merged or changed from the source")
