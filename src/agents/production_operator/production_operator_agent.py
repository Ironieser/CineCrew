#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
ProductionOperator Agent [Controller] — FilmDSL Layer 4 + (optional) execution.

1. build_from_blueprint()
     render_layer (resolved prompts) -> VideoJobBatch + assembly_layer. No network.
     Dialogue shots are split into prelude / dialogue_core / afterglow segments whose
     durations sum to the shot's duration (short, well-formed clips for DiT video models; nothing under 1 s).

2. execute_jobs()  — opt-in ReAct loop over the OpenAI-style backends
     for each shot : keyframe  = T2I / TI2I(resolved prompt [+ character reference sheets])
                     VisualJudge(keyframe) -> accept | retry with the judge's revised prompt
     for each job  : clip      = I2V(keyframe, resolved_i2v)
                     VisualJudge(sampled frames) -> accept | retry
      post          : clips cut together in order (ffmpeg concat, fade-in on the first shot)
     Results are written back into the blueprint: keyframe_image_path, video_clip_path(s),
     visual_review, final_film_path, and the prompt that finally rendered.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

from ...adapters import media_tools
from ...adapters.video_client import VideoClient, VideoResult
from ...config import Config
from ...schemas.assets import AssetLibrary
from ...schemas.blueprint import SceneBlueprint, ShotBlueprint, AssemblyLayer, AudioTrack
from ...schemas.video_jobs import VideoJob, VideoJobBatch, DEFAULT_NEGATIVE_PROMPT

MIN_SEGMENT_SECONDS = 1.0  # DiT video models degrade below ~1 s; matches the DSL validator's floor


class ProductionOperatorAgent:
    """Controller: assembles VideoJobs from the blueprint; runs them through the adapters on request."""

    def __init__(self, fps: Optional[int] = None):
        self.fps = fps or Config.VIDEO_FPS
        # Backend clients / the judge are created lazily: build_from_blueprint() needs none of them.
        self._video: Optional[VideoClient] = None
        self._t2i = None
        self._judge = None

    # ─────────────────────────────────────────────────────────────────────
    # Layer 4: VideoJobBatch + assembly_layer
    # ─────────────────────────────────────────────────────────────────────

    def build_from_blueprint(
        self,
        blueprint: SceneBlueprint,
        asset_library: AssetLibrary,
        segment_dialogue: bool = True,
    ) -> VideoJobBatch:
        """
        Read each shot's render_layer.video.resolved_i2v, build the VideoJobBatch, and write
        assembly_layer (transition + audio-track metadata) back into the blueprint.

        segment_dialogue: split dialogue shots into prelude / dialogue_core / afterglow jobs (default).
        False keeps one job per shot that carries the line — for joint audio-video backends that
        voice the dialogue themselves and must not have a sentence cut across clips.
        Every job's `extra` carries `reference_images` / `reference_subjects` (all on-screen characters with
        a reference image: path, asset_id, name, appearance) and the dialogue `speaker` name, so a
        multi-reference backend can condition on every character and attribute the spoken line.

        Precondition: TechnicalDirectorAgent has filled render_layer (DailiesReviewer may have refined it).
        """
        print(
            f"--- [ProductionOperator] Building VideoJobBatch from Blueprint ({len(blueprint.shots)} shots) ---",
            flush=True,
        )
        sys.stdout.flush()

        # Render target comes from the blueprint's Layer-0 metadata (set from Config at init).
        width, height = _parse_size(blueprint.metadata.target_resolution or Config.VIDEO_SIZE)
        fps = blueprint.metadata.global_fps or self.fps
        jobs: List[VideoJob] = []
        scene_id = blueprint.blueprint_id

        for i, shot in enumerate(blueprint.shots):
            render = shot.render_layer
            if render and render.video.resolved_i2v:
                base_prompt = render.video.resolved_i2v
            else:
                print(f"   ⚠️  [{shot.shot_id}] render_layer.video.resolved_i2v missing, using fallback.", flush=True)
                base_prompt = self._blueprint_fallback_prompt(shot, blueprint.global_style)
            cont = shot.narrative_layer.continuity
            if cont is not None:   # continuity ledger (ScriptSupervisor) rides on every job's prompt
                from ..script_supervisor import continuity_sentence
                on = {e.asset_id for e in (shot.staging_layer.entities if shot.staging_layer else [])}
                if render and render.image and render.image.characters_in_shot:
                    on |= set(render.image.characters_in_shot)
                base_prompt = f"{base_prompt}\n{continuity_sentence(cont, asset_library, on)}"

            # I2V reference: the rendered keyframe if execution already produced one,
            # otherwise the first character's reference sheet.
            image_ref: Optional[str] = None
            if render:
                image_ref = render.image.keyframe_image_path
                if not image_ref and render.image.conditioning:
                    ccs = render.image.conditioning.character_consistency
                    if ccs and ccs[0].reference_image_paths:
                        image_ref = ccs[0].reference_image_paths[0]

            ref_subjects = []  # every on-screen character with a reference image, for multi-reference backends
            for c in (render.image.conditioning.character_consistency if render and render.image.conditioning else []):
                ch = asset_library.get_character_by_id(c.asset_id)
                for p in c.reference_image_paths:
                    ref_subjects.append({
                        "image": p, "asset_id": c.asset_id, "name": ch.name if ch else c.asset_id,
                        "appearance": " ".join(x for x in [ch.description, ch.clothing_style] if x) if ch else "",
                    })
            all_refs = [r["image"] for r in ref_subjects]

            total_duration = shot.staging_layer.duration_seconds
            dialogue = shot.narrative_layer.dialogue
            speaker = asset_library.get_character_by_id(dialogue.speaker_asset_id) if dialogue.speaker_asset_id else None
            voice_instructions = _voice_instructions(speaker, shot)
            if dialogue.has_dialogue and dialogue.text and not segment_dialogue:
                segment_durations, segment_roles = [total_duration], ["dialogue_core"]
            elif dialogue.has_dialogue and dialogue.text:
                core_hint = self._estimate_dialogue_duration(dialogue.text)
                segment_durations = self._split_dialogue_shot_duration(total_duration, core_hint=core_hint)
                segment_roles = ["prelude", "dialogue_core", "afterglow"][: len(segment_durations)]
            else:
                segment_durations, segment_roles = [total_duration], ["single"]

            for seg_dur, role in zip(segment_durations, segment_roles):
                if seg_dur <= 0:
                    continue
                jobs.append(
                    VideoJob(
                        job_id=f"{scene_id}_{shot.shot_id}_{role}",
                        scene_id=scene_id,
                        shot_id=shot.shot_id,
                        segment_id=f"{shot.shot_id}_{role}",
                        prompt=base_prompt + (_SEGMENT_HINT.get(role, "") if segment_dialogue else ""),
                        negative_prompt=(
                            render.image.negative_prompt
                            if render and render.image.negative_prompt is not None
                            else DEFAULT_NEGATIVE_PROMPT
                        ),
                        image_reference=image_ref,
                        dialogue=dialogue.text if role == "dialogue_core" else None,
                        voice=(dialogue.voice_preset or (speaker.voice_preset_id if speaker else None)) if role == "dialogue_core" else None,
                        voice_instructions=voice_instructions if role == "dialogue_core" else None,
                        duration=seg_dur,
                        width=width,
                        height=height,
                        fps=fps,
                        frame_num=self.calculate_frame_num(seg_dur, fps),
                        seed=render.image.seed if render else None,
                        extra={
                            "role": role,
                            "reference_images": all_refs,
                            "reference_subjects": ref_subjects,
                            "speaker": (speaker.name if speaker else None) if role == "dialogue_core" else None,
                        },
                    )
                )

            self._write_assembly_layer(shot, i)

        batch = VideoJobBatch(
            scene_id=scene_id,
            jobs=jobs,
            total_shots=len(jobs),
            estimated_duration=sum(s.staging_layer.duration_seconds for s in blueprint.shots),
        )
        print(f"   ✅ VideoJobBatch built: {len(jobs)} jobs, total_duration={batch.estimated_duration:.1f}s", flush=True)
        return batch

    @staticmethod
    def calculate_frame_num(duration: float, fps: int = 16) -> int:
        """Frame count of the form 4n+1 (the common constraint of DiT video models such as Wan 2.2)."""
        base = int(duration * fps)
        if (base - 1) % 4 == 0:
            return base
        return 4 * ((base - 1) // 4 + 1) + 1

    # ─────────────────────────────────────────────────────────────────────
    # Execution: keyframe -> judge -> clip -> judge (ReAct loop)
    # ─────────────────────────────────────────────────────────────────────

    def execute_jobs(
        self,
        batch: VideoJobBatch,
        output_dir,
        blueprint: Optional[SceneBlueprint] = None,
        *,
        judge: bool = True,
        max_retries: int = 1,
        keyframes: bool = True,
        stitch: bool = True,
        parallel: int = 1,
        library: Optional[AssetLibrary] = None,
        keyframe_retries: Optional[int] = None,
    ) -> List[VideoResult]:
        """
        Run the batch on the T2I_* / VIDEO_* backends.

        judge        : score every keyframe / clip with the VLM VisualJudge and retry rejected
                       ones (at most `max_retries` extra attempts each) using its revised prompt.
        keyframes    : render a keyframe per shot first (TI2I with the character sheets when
                       available) and use it as the I2V reference; False -> reference sheets only.
        parallel     : clips rendered concurrently (one per backend replica behind VIDEO_BASE_URL); each clip's
                       render -> judge -> retry loop stays sequential, results keep job order.
        library      : AssetLibrary for the keyframe FrameCheck (identity vs sheets, cast, world facts)
        keyframe_retries : extra keyframe attempts (default max_retries); frames are cheap, so this can be higher
        stitch       : cut all clips together in shot order (ffmpeg) into <output_dir>/film.mp4,
                       honouring the first shot's fade_in; path stored in blueprint.final_film_path.
        Returns one VideoResult per job; blueprint (if given) is updated in place.
        """
        out = Path(output_dir)
        by_shot: Dict[str, ShotBlueprint] = {s.shot_id: s for s in blueprint.shots} if blueprint else {}
        global_style = blueprint.global_style if blueprint else ""

        if keyframes and blueprint:
            print(f"--- [ProductionOperator] Keyframes for {len(blueprint.shots)} shots (judge={judge}) ---", flush=True)
            todo_shots = {j.shot_id for j in batch.jobs}
            kf = lambda shot: self._render_keyframe(shot, out / "keyframes", judge,
                                                    max_retries if keyframe_retries is None else keyframe_retries,
                                                    global_style, library)
            shots = [s for s in blueprint.shots if s.render_layer is not None and s.shot_id in todo_shots]
            if parallel > 1 and len(shots) > 1:
                from concurrent.futures import ThreadPoolExecutor
                self._t2i_client()
                with ThreadPoolExecutor(max_workers=parallel) as pool:
                    list(pool.map(kf, shots))
            else:
                for shot in shots:
                    kf(shot)
            for job in batch.jobs:
                shot = by_shot.get(job.shot_id)
                if shot and shot.render_layer and shot.render_layer.image.keyframe_image_path:
                    job.image_reference = shot.render_layer.image.keyframe_image_path
                    job.extra["keyframe"] = shot.render_layer.image.keyframe_image_path   # backend: first / reference frame

        print(f"--- [ProductionOperator] Clips for {len(batch.jobs)} jobs (judge={judge}) ---", flush=True)
        render = lambda job: self._render_clip(job, by_shot.get(job.shot_id), out, judge, max_retries, global_style)
        if parallel > 1 and len(batch.jobs) > 1:
            from concurrent.futures import ThreadPoolExecutor
            self._video_client()
            if judge:
                self._visual_judge()   # create the shared clients before the worker threads use them
            with ThreadPoolExecutor(max_workers=parallel) as pool:
                results = list(pool.map(render, batch.jobs))
        else:
            results = [render(job) for job in batch.jobs]

        for shot in by_shot.values():
            if shot.render_layer is None:
                continue
            paths = [r.video_path for r in results if r.shot_id == shot.shot_id and r.video_path]
            shot.render_layer.video.video_clip_paths = paths
            shot.render_layer.video.video_clip_path = paths[0] if paths else None

        done = sum(1 for r in results if r.status == "completed")
        print(f"   ✅ Execution finished: {done}/{len(results)} clips", flush=True)

        if stitch and blueprint and done:
            film = self.stitch(blueprint, out / "film.mp4")
            if film:
                print(f"   🎞  Film assembled: {film}", flush=True)
        return results

    @staticmethod
    def stitch(blueprint: SceneBlueprint, out_path: Path) -> Optional[Path]:
        """Post: concatenate every rendered clip in shot/segment order (assembly_layer transitions)."""
        clips: List[str] = []
        for shot in blueprint.shots:
            if shot.render_layer is not None:
                clips.extend(shot.render_layer.video.video_clip_paths)
        if not clips:
            return None
        first = blueprint.shots[0].assembly_layer
        fade_in = 0.5 if (first and first.transition_in == "fade_in") else 0.0
        film = media_tools.concat_clips([Path(c) for c in clips], Path(out_path), fade_in=fade_in)
        if film:
            blueprint.final_film_path = str(film)
        return film

    def _render_keyframe(self, shot: ShotBlueprint, out_dir: Path, judge: bool, max_retries: int, global_style: str,
                         library: Optional[AssetLibrary] = None) -> None:
        """
        Keyframe-first: render the shot's opening frame (TI2I with the characters' reference sheets), check it with the
        specific FrameCheck gates (identity, strangers, world facts, text, time of day), and iterate — frames are cheap
        next to clips — feeding the found problems back into the prompt. The best frame (fewest failures) is kept and
        becomes the clip's first frame / reference frame.
        """
        img = shot.render_layer.image
        refs = [
            p
            for c in (img.conditioning.character_consistency if img.conditioning else [])
            for p in c.reference_image_paths
            if Path(p).exists()
        ]
        prompt = img.resolved_ti2i if (refs and img.resolved_ti2i) else img.resolved_t2i
        if not prompt:
            return
        # props staged in this shot that have a reference picture (critical first): exact look, e.g. a code-rendered
        # planet whose night side must be dark
        if library is not None and shot.staging_layer:
            staged = [library.get_prop_by_id(e.asset_id) for e in shot.staging_layer.entities
                      if hasattr(library, "get_prop_by_id")]
            staged = [p for p in staged if p and p.visual_references and p.visual_references.canonical_image_path
                      and Path(p.visual_references.canonical_image_path).exists()]
            staged.sort(key=lambda p: {"critical": 0, "supporting": 1}.get(p.importance, 2))
            for p in staged:
                if len(refs) >= 3:
                    break
                refs = refs + [p.visual_references.canonical_image_path]
                prompt = (f"{prompt}\nPicture {len(refs)} is the {p.name}: reproduce it exactly as shown "
                          f"(shape, lit and dark parts, colours).")
        # the location's establishing shot as one more reference: the same set in every shot of the scene
        env = shot.staging_layer.environment_id if shot.staging_layer else None
        loc = library.get_location_by_id(env) if (library and env and hasattr(library, "get_location_by_id")) else None
        loc_img = loc.visual_references.canonical_image_path if (loc and loc.visual_references) else None
        if loc_img and Path(loc_img).exists() and len(refs) < 3:
            refs = refs + [loc_img]
            prompt = (f"{prompt}\nPicture {len(refs)} is the location ({loc.name}): keep its set, layout, "
                      f"windows and lighting; it contains no people.")
        if not refs:   # nothing to condition the frame on: let the video model compose the shot from text
            return
        cont = shot.narrative_layer.continuity
        if cont is not None and library is not None:   # the frame obeys the ledger and the film's world facts too
            from ..script_supervisor import continuity_sentence
            on = set(img.characters_in_shot or [])
            prompt = f"{prompt}\n{continuity_sentence(cont, library, on)}"
        expected = list(img.characters_in_shot or [])
        names = {c.id: c.name for c in library.characters} if library else {}
        review_log: List[dict] = []
        best: Optional[tuple] = None                     # (n_failures, path, prompt)
        base_prompt = prompt
        for attempt in range(max_retries + 1):
            path = out_dir / f"{shot.shot_id}_kf{attempt}.png"
            print(f"   🖼  [{shot.shot_id}] keyframe attempt {attempt + 1} ({'TI2I' if refs else 'T2I'})", flush=True)
            try:
                self._t2i_client().render_to_file(
                    path, prompt=prompt, negative_prompt=img.negative_prompt or "",
                    reference_images=refs or None, size=Config.T2I_KEYFRAME_SIZE,
                    seed=(img.seed or 0) + 7919 * attempt,
                )
            except Exception as e:
                print(f"      ❌ T2I failed: {type(e).__name__}: {e}", flush=True)
                review_log.append({"attempt": attempt, "error": f"{type(e).__name__}: {e}"})
                continue
            if not judge or library is None:
                best = (0, path, prompt)
                break
            try:
                from ..dailies_reviewer.frame_check import FrameCheckAgent
                fc = FrameCheckAgent().check(str(path), shot, library, expected)
                fails = FrameCheckAgent.failures(fc, shot, [names.get(c, c) for c in expected])
            except Exception as e:
                print(f"      ⚠️  frame check failed ({e}); keeping this keyframe", flush=True)
                review_log.append({"attempt": attempt, "check_error": str(e)})
                best = best or (99, path, prompt)
                break
            review_log.append({"attempt": attempt, "path": str(path), "failures": fails, **fc.model_dump()})
            if best is None or len(fails) < best[0]:
                best = (len(fails), path, prompt)
            if not fails:
                print(f"      ✅ keyframe passes all frame checks", flush=True)
                break
            print(f"      ✏️  keyframe fails: {'; '.join(fails)[:180]}", flush=True)
            # prompt repair from the specific findings (not a free rewrite: the plan's prompt stays the base)
            prompt = f"{base_prompt}\nFix: {'; '.join(fails)}. {fc.fix}".strip()

        if best is not None:
            img.keyframe_image_path = str(best[1])
            if refs and img.resolved_ti2i:
                img.resolved_ti2i = best[2]
            else:
                img.resolved_t2i = best[2]
        vr = shot.render_layer.visual_review or {}
        vr["keyframe"] = review_log[-1] if review_log else None
        vr["keyframe_attempts"] = review_log
        shot.render_layer.visual_review = vr

    def _render_clip(
        self,
        job: VideoJob,
        shot: Optional[ShotBlueprint],
        out: Path,
        judge: bool,
        max_retries: int,
        global_style: str,
    ) -> VideoResult:
        video = self._video_client()
        review_log: List[dict] = []
        result: Optional[VideoResult] = None
        best: Optional[tuple] = None          # (score, result): if no attempt is accepted, keep the best one, not the last
        for attempt in range(max_retries + 1):
            if attempt and job.seed is not None:
                job.seed += 1
            clip_dir = out / "clips" if attempt == 0 else out / "clips" / f"retry_{attempt}"
            result = video.generate(job, clip_dir)
            if result.status != "completed":
                review_log.append({"attempt": attempt, "error": result.error})
                continue
            if not judge or shot is None:
                break
            frames = video.sample_frames(result.video_id, Path(result.video_path), out / "frames", n=4)
            if not frames:
                review_log.append({"attempt": attempt, "judge_skipped": "no frames available (no spritesheet, no ffmpeg)"})
                break
            try:
                review = self._visual_judge().review_clip([str(f) for f in frames], shot, job.prompt, global_style)
            except Exception as e:
                review_log.append({"attempt": attempt, "judge_error": str(e)})
                break
            review_log.append({"attempt": attempt, "segment_id": job.segment_id, "video_path": result.video_path,
                               **review.model_dump()})
            if best is None or review.score > best[0]:
                best = (review.score, result)
            if review.accepted:
                print(f"      ✅ clip accepted (score {review.score:.2f})", flush=True)
                break
            print(f"      ✏️  clip rejected (score {review.score:.2f}): {'; '.join(review.issues)[:160]}", flush=True)
            if review.revised_prompt:
                job.prompt = review.revised_prompt
        else:
            if best is not None and best[1] is not result:
                print(f"      ↩️  no attempt accepted; keeping the best (score {best[0]:.2f})", flush=True)
                result = best[1]

        if shot is not None and shot.render_layer is not None:
            vr = shot.render_layer.visual_review or {}
            vr.setdefault("clips", []).append({"segment_id": job.segment_id, "attempts": review_log})
            shot.render_layer.visual_review = vr
        return result

    # ── lazy clients ──────────────────────────────────────────────────────

    def _video_client(self) -> VideoClient:
        if self._video is None:
            self._video = VideoClient()
        return self._video

    def _t2i_client(self):
        if self._t2i is None:
            from ...adapters.t2i_client import T2IClient
            self._t2i = T2IClient()
        return self._t2i

    def _visual_judge(self):
        if self._judge is None:
            from ..dailies_reviewer.visual_judge import VisualJudgeAgent
            self._judge = VisualJudgeAgent()
        return self._judge

    # ─────────────────────────────────────────────────────────────────────
    # Assembly layer + helpers
    # ─────────────────────────────────────────────────────────────────────

    def _write_assembly_layer(self, shot: ShotBlueprint, shot_index: int) -> None:
        """
        Assembly metadata for the post stage: the audio tracks of the shot (dialogue via
        the speaker's TTS voice preset, BGM) and the transition rule (fade in on the first
        shot, cuts elsewhere).
        """
        if shot.assembly_layer is not None:
            return
        audio_tracks: List[AudioTrack] = []
        dialogue = shot.narrative_layer.dialogue
        if dialogue.has_dialogue and dialogue.text:
            audio_tracks.append(
                AudioTrack(
                    track_id=f"{shot.shot_id}_dialogue",
                    type="dialogue",
                    source=dialogue.voice_preset or "tts_default",
                    description=dialogue.text[:80],
                )
            )
        audio_tracks.append(
            AudioTrack(track_id=f"{shot.shot_id}_bgm", type="bgm", source="bgm_auto", description="Auto-assigned background music")
        )
        shot.assembly_layer = AssemblyLayer(
            transition_in="fade_in" if shot_index == 0 else "cut",
            transition_out="cut",
            audio_tracks=audio_tracks,
        )

    @staticmethod
    def _blueprint_fallback_prompt(shot: ShotBlueprint, global_style: str) -> str:
        staging, narrative = shot.staging_layer, shot.narrative_layer
        parts = [global_style, narrative.narrative_action]
        if staging.camera.movement:
            parts.append(f"Camera: {staging.camera.movement}.")
        if narrative.dialogue.text:
            parts.append(f'Lip-sync: "{narrative.dialogue.text}".')
        return " ".join(p for p in parts if p).strip()

    @staticmethod
    def _split_dialogue_shot_duration(total_duration: float, core_hint: Optional[float] = None) -> List[float]:
        """
        Split a dialogue shot into prelude / dialogue_core / afterglow.
        The parts sum exactly to total_duration and each is >= MIN_SEGMENT_SECONDS; when
        the shot is short, or the line nearly fills it, the shot stays one segment.
        """
        m = MIN_SEGMENT_SECONDS
        if total_duration < 3 * m:
            return [total_duration]
        if core_hint is not None and core_hint > 0:
            core = max(m, core_hint + 0.4)              # the spoken line plus a little air
            if total_duration - core < 2 * m:
                return [total_duration]                 # no room for a real lead-in and reaction
        else:
            core = min(0.5 * total_duration, total_duration - 2 * m)   # leave >= m for lead-in and reaction
        remaining = total_duration - core
        pre = max(m, remaining * 2.0 / 3.0)             # lead-in slightly longer than the reaction
        post = remaining - pre
        if post < m:                                    # remaining >= 2m, so pre stays >= m
            post, pre = m, remaining - m
        return [pre, core, post]

    @staticmethod
    def _estimate_dialogue_duration(text: str) -> float:
        """~3 words per second (whitespace tokens; CJK text is estimated at 4 characters/s)."""
        if not text:
            return 0.0
        words = text.split()
        if len(words) <= 1 and len(text) > 8:
            return len(text) / 4.0
        return len(words) / 3.0


_SEGMENT_HINT = {
    "prelude": " This segment covers the lead-in before the line is spoken; the character may prepare physically but does NOT start the main dialogue yet.",
    "dialogue_core": " This segment contains the main spoken line; keep the performance focused on delivering the dialogue.",
    "afterglow": " This segment shows the silent reaction and emotional afterglow immediately after the line finishes; no new dialogue is spoken.",
}


def _voice_instructions(speaker, shot: ShotBlueprint) -> Optional[str]:
    """Voice identity + performed emotion, for a joint audio-video backend or a TTS stage."""
    parts = []
    if speaker is not None and speaker.voice_design:
        parts.append(speaker.voice_design.strip())
    elif speaker is not None and speaker.voice_description:
        parts.append(f"Voice: {speaker.voice_description}")
    n = shot.narrative_layer
    if n and n.performance_emotion:
        parts.append(f"Emotion: {n.performance_emotion}" + (f" ({n.performance_intensity}/10)" if n.performance_intensity else ""))
    return "\n".join(parts) or None


def _parse_size(size: str) -> tuple:
    try:
        w, h = size.lower().replace("*", "x").split("x")
        return int(w), int(h)
    except Exception:
        return 1280, 720
