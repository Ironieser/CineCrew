#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
DailiesReviewer — closed-loop quality review of resolved prompts.

Reads a completed SceneBlueprint (render_layer filled with resolved T2I/I2V
prompts) and runs a sliding 5-shot window critic that evaluates and optionally
fixes each shot's prompts. This repeats for several rounds (coarse-to-fine).

Loop semantics:
  - Each round works from a snapshot of the blueprint taken at the round start,
    so every shot sees its neighbours in a consistent (pre-round) state rather
    than a mix of already-fixed and not-yet-fixed neighbours.
  - A round is counted as making a change only when a fix actually alters a
    prompt (not merely when the critic flags needs_fix). The loop stops early
    once a round changes nothing — true convergence, not just inactivity.
  - A shot that passed review and whose 5-shot window is unchanged from the
    previous round is skipped (no redundant LLM call).
  - Image fixes are applied atomically: resolved_t2i and resolved_ti2i are
    never left divergent.

ProductionOperator is then re-run on the refined blueprint to rebuild VideoJobBatch.
"""

from pathlib import Path

import hashlib
import json
from typing import Optional

from ...engine import ConfigurableAgent
from ...schemas.assets import AssetLibrary
from ...schemas.blueprint import SceneBlueprint, ShotBlueprint
from ...schemas.critic import ShotCriticResult

_WINDOW_RADIUS = 2       # shots on each side of the current shot
DEFAULT_MAX_ROUNDS = 2   # coarse-to-fine refinement passes (stops early on convergence)


def _window_signature(current: dict, neighbours: list) -> str:
    """Stable hash of a shot's 5-shot window (current + neighbours). Two rounds
    with the same signature mean the shot's review context did not change."""
    payload = json.dumps([current, neighbours], ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


_HERE = Path(__file__).resolve().parent


class DailiesReviewerAgent:
    """
    Closed-loop sliding-window reviewer that refines resolved prompts in a Blueprint.

    Usage:
        agent = DailiesReviewerAgent()
        refined_blueprint, report = agent.run(blueprint, asset_library)
    """

    def __init__(self):
        self._reviewer = ConfigurableAgent(config_path=str(_HERE / "dailies_reviewer.yaml"))

    def run(
        self,
        blueprint: SceneBlueprint,
        asset_library: Optional[AssetLibrary] = None,
        max_rounds: int = DEFAULT_MAX_ROUNDS,
    ) -> tuple[SceneBlueprint, dict]:
        """
        Refine the blueprint over up to `max_rounds` review passes.

        Stops early once a full pass changes nothing (converged).

        Returns:
            (refined_blueprint, report)
            report = {rounds: [...per-round stats...], total_rounds, total_fixed, total_errored}
        """
        # shot_id -> window signature when the shot last passed review unchanged.
        stable: dict[str, str] = {}
        rounds: list[dict] = []
        for r in range(1, max_rounds + 1):
            stats = self._review_once(blueprint, asset_library, round_idx=r, stable=stable)
            rounds.append(stats)
            # Converge only when a full pass made no changes AND hit no errors, so a
            # transient reviewer failure gets another attempt (bounded by max_rounds).
            if stats["fixed"] == 0 and stats["errored"] == 0:
                print(f"--- [DailiesReviewer] Converged after round {r} (no changes) ---", flush=True)
                break
        return blueprint, {
            "rounds": rounds,
            "total_rounds": len(rounds),
            "total_fixed": sum(s["fixed"] for s in rounds),
            "total_errored": sum(s["errored"] for s in rounds),
        }

    def _review_once(
        self,
        blueprint: SceneBlueprint,
        asset_library: Optional[AssetLibrary],
        round_idx: int,
        stable: dict,
    ) -> dict:
        """One sliding-window pass over every shot, working from a round-start snapshot."""
        shots = blueprint.shots
        global_style = blueprint.global_style or (
            asset_library.global_style if asset_library else ""
        )
        # Snapshot every shot once at the start of the round (consistent context + no re-serialisation).
        summaries = [s.summary_dict() for s in shots]

        stats = {
            "round": round_idx,
            "total": len(shots),
            "fixed": 0,           # prompts actually changed
            "unchanged": 0,       # reviewed, no real change
            "reused_stable": 0,   # skipped: passed before and window unchanged
            "errored": 0,         # reviewer LLM call failed
            "skipped_no_render": 0,
            "fixes": [],
        }

        print(
            f"--- [DailiesReviewer] Round {round_idx}: reviewing {len(shots)} shots "
            f"(window radius={_WINDOW_RADIUS}) ---",
            flush=True,
        )

        for idx, shot in enumerate(shots):
            if shot.render_layer is None:
                stats["skipped_no_render"] += 1
                continue

            # Build the 5-shot window from the snapshot (neighbours labelled by offset).
            lo = max(0, idx - _WINDOW_RADIUS)
            hi = min(len(shots), idx + _WINDOW_RADIUS + 1)
            neighbours = []
            for j in range(lo, hi):
                if j == idx:
                    continue
                s = dict(summaries[j])
                offset = j - idx
                s["_role"] = f"prev_{abs(offset)}" if offset < 0 else f"next_{offset}"
                neighbours.append(s)

            sig = _window_signature(summaries[idx], neighbours)
            # Skip shots that already passed and whose window has not changed since.
            if stable.get(shot.shot_id) == sig:
                stats["reused_stable"] += 1
                continue

            context_json = json.dumps(neighbours, ensure_ascii=False, indent=2)
            current_json = json.dumps(summaries[idx], ensure_ascii=False, indent=2)

            try:
                result: ShotCriticResult = self._reviewer.run(
                    global_style=global_style,
                    context_shots_json=context_json,
                    current_shot_json=current_json,
                )
            except Exception as e:
                print(f"   ⚠️  [{shot.shot_id}] reviewer LLM failed: {e}. Will retry next round.", flush=True)
                stats["errored"] += 1
                continue  # do NOT mark stable: this shot was never successfully reviewed

            if result.needs_fix and self._apply_fix(shot, result):
                stats["fixed"] += 1
                stats["fixes"].append({"shot_id": shot.shot_id, "issues": result.issues})
                print(f"   ✏️  [{shot.shot_id}] FIXED — {result.issues}", flush=True)
                # changed → its window signature will differ next round, so re-reviewed then
            else:
                # reviewed and either no fix needed, or the "fix" was a no-op → stable
                stats["unchanged"] += 1
                stable[shot.shot_id] = sig

        print(
            f"--- [DailiesReviewer] Round {round_idx} done: {stats['fixed']} changed, "
            f"{stats['unchanged']} ok, {stats['reused_stable']} skipped(stable), "
            f"{stats['errored']} errored, {stats['skipped_no_render']} no-render ---",
            flush=True,
        )
        return stats

    @staticmethod
    def _apply_fix(shot: ShotBlueprint, result: ShotCriticResult) -> bool:
        """Write reviewer fixes into the shot's render_layer in place.

        Returns True only if a prompt actually changed. Image fixes are applied
        atomically: resolved_t2i and resolved_ti2i are never left divergent —
        if the critic fixes t2i without supplying a ti2i fix while a ti2i prompt
        exists, the image fix is skipped (kept consistent) rather than applied
        half-way.
        """
        render = shot.render_layer
        if render is None:
            return False
        changed = False

        # ── Image (resolved_t2i / resolved_ti2i): atomic ──
        if result.fixed_resolved_t2i is not None:
            has_ti2i = render.image.resolved_ti2i is not None
            if has_ti2i and result.fixed_resolved_ti2i is None:
                print(
                    f"   ⚠️  [{shot.shot_id}] t2i fix given without a matching ti2i fix; "
                    f"skipping image fix to keep t2i/ti2i consistent.",
                    flush=True,
                )
            else:
                if result.fixed_resolved_t2i != render.image.resolved_t2i:
                    render.image.resolved_t2i = result.fixed_resolved_t2i
                    changed = True
                if (
                    result.fixed_resolved_ti2i is not None
                    and result.fixed_resolved_ti2i != render.image.resolved_ti2i
                ):
                    render.image.resolved_ti2i = result.fixed_resolved_ti2i
                    changed = True
        elif result.fixed_resolved_ti2i is not None:
            if result.fixed_resolved_ti2i != render.image.resolved_ti2i:
                render.image.resolved_ti2i = result.fixed_resolved_ti2i
                changed = True

        # ── Video (resolved_i2v): independent ──
        if (
            result.fixed_resolved_i2v is not None
            and result.fixed_resolved_i2v != render.video.resolved_i2v
        ):
            render.video.resolved_i2v = result.fixed_resolved_i2v
            changed = True

        return changed
