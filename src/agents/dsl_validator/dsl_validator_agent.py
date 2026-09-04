#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
DSL Validator Agent [Controller] — guards the Asset-ID contract of the FilmDSL.

Validate (skill) -> deterministic ID repair (skill) -> LLM repair of the shots that are
still broken (dsl_validator.yaml, staging only) -> re-validate -> drop what is still
unknown, so no downstream stage ever sees an ID that is not in the AssetLibrary.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field

from ...engine import ConfigurableAgent
from ...schemas.assets import AssetLibrary
from ...schemas.blueprint import SceneBlueprint
from ...schemas.blueprint_partial import ShotStagingList
from ...skills.asset_context import build_asset_context
from ...skills.dsl_validation import validate_blueprint, auto_correct_ids, drop_unknown_ids

_HERE = Path(__file__).resolve().parent


class ValidationIssue(BaseModel):
    shot_id: str
    issue_type: str
    field_name: str
    current_value: str
    severity: str = Field(description="critical | warning")
    suggested_fix: str | None = None


class ValidationReport(BaseModel):
    total_shots: int
    issues: List[ValidationIssue] = Field(default_factory=list, description="Issues remaining after repair")
    critical_count: int = 0
    warning_count: int = 0
    auto_fixes: List[Dict[str, Any]] = Field(default_factory=list, description="Deterministic ID remaps applied")
    llm_repaired_shots: List[str] = Field(default_factory=list, description="Shots whose staging the LLM rewrote")
    dropped: List[Dict[str, Any]] = Field(default_factory=list, description="References removed as a last resort")

    @classmethod
    def from_issues(cls, issue_dicts: List[Dict[str, Any]], total_shots: int) -> "ValidationReport":
        report = cls(total_shots=total_shots)
        for d in issue_dicts:
            issue = ValidationIssue(**d)
            report.issues.append(issue)
            if issue.severity == "critical":
                report.critical_count += 1
            elif issue.severity == "warning":
                report.warning_count += 1
        return report


class DSLValidatorAgent:
    """Controller: Blueprint -> ValidationReport, repairing critical ID errors on the way."""

    def __init__(self):
        self._fix_agent = ConfigurableAgent(config_path=str(_HERE / "dsl_validator.yaml"))

    def run(
        self,
        blueprint: SceneBlueprint,
        asset_library: AssetLibrary,
        auto_correct: bool = True,
    ) -> Tuple[SceneBlueprint, ValidationReport]:
        total = len(blueprint.shots)
        issues = validate_blueprint(blueprint, asset_library)
        report = ValidationReport.from_issues(issues, total)
        print(
            f"   🔍 [DSLValidator] {total} shots — {report.critical_count} critical, {report.warning_count} warnings",
            flush=True,
        )
        for issue in report.issues[:10]:
            print(f"      {'❌' if issue.severity == 'critical' else '⚠️ '} [{issue.shot_id}] {issue.issue_type}: {issue.current_value}", flush=True)

        if not (auto_correct and report.critical_count):
            return blueprint, report

        # 1) deterministic: near-miss IDs (case / prefix / substring)
        fixes = auto_correct_ids(blueprint, asset_library)
        issues = validate_blueprint(blueprint, asset_library)

        # 2) LLM: only the shots that are still broken, staging layer only
        broken = sorted({i["shot_id"] for i in issues if i["severity"] == "critical" and i["issue_type"] != "duplicate_shot_id"})
        repaired: List[str] = []
        if broken:
            print(f"      🔧 LLM repair for {len(broken)} shot(s): {broken}", flush=True)
            try:
                repaired = self._llm_repair(blueprint, asset_library, broken, issues)
            except Exception as e:
                print(f"      ⚠️  LLM repair failed: {e}", flush=True)
            issues = validate_blueprint(blueprint, asset_library)

        # 3) last resort: never hand a dangling ID downstream
        dropped: List[Dict[str, Any]] = []
        if any(i["severity"] == "critical" for i in issues):
            dropped = drop_unknown_ids(blueprint, asset_library)
            issues = validate_blueprint(blueprint, asset_library)

        report = ValidationReport.from_issues(issues, total)
        report.auto_fixes, report.llm_repaired_shots, report.dropped = fixes, repaired, dropped
        print(
            f"      ✅ after repair: {report.critical_count} critical, {report.warning_count} warnings "
            f"({len(fixes)} remapped, {len(repaired)} LLM-repaired, {len(dropped)} dropped)",
            flush=True,
        )
        return blueprint, report

    def _llm_repair(
        self,
        blueprint: SceneBlueprint,
        asset_library: AssetLibrary,
        shot_ids: List[str],
        issues: List[Dict[str, Any]],
    ) -> List[str]:
        """Ask the LLM for corrected staging_layers of the listed shots; write them back by shot_id."""
        wanted = set(shot_ids)
        shots_json = json.dumps(
            [
                {
                    "shot_id": s.shot_id,
                    "narrative_layer": s.narrative_layer.model_dump() if s.narrative_layer else {},
                    "staging_layer": s.staging_layer.model_dump() if s.staging_layer else {},
                }
                for s in blueprint.shots
                if s.shot_id in wanted
            ],
            ensure_ascii=False,
            indent=2,
        )
        issues_json = json.dumps([i for i in issues if i["shot_id"] in wanted], ensure_ascii=False, indent=2)
        result: ShotStagingList = self._fix_agent.run(
            shots_json=shots_json,
            validation_issues=issues_json,
            asset_context=build_asset_context(asset_library),
        )
        fixed = {item.shot_id: item.staging_layer for item in result.shots if item.shot_id in wanted}
        for shot in blueprint.shots:
            if shot.shot_id in fixed:
                shot.staging_layer = fixed[shot.shot_id]
        return sorted(fixed)
