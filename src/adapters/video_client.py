#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
VideoClient: OpenAI-style video generation adapter (T2V / I2V).

Speaks the OpenAI Videos API through the official SDK:

    POST {base_url}/videos                  create  (prompt, model, size, seconds, input_reference)
    GET  {base_url}/videos/{id}             poll    (status: queued | in_progress | completed | failed)
    GET  {base_url}/videos/{id}/content     download (mp4 bytes)

Anything that is not part of the OpenAI schema (negative_prompt, fps, frame_num,
seed, ...) is sent in the request body via `extra_body`, so a self-hosted server
(e.g. a Wan 2.2 / LTX / CogVideoX wrapper) can pick it up while a strict OpenAI
endpoint simply ignores it. Pure adapter: no prompt engineering here.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..config import Config
from ..schemas.video_jobs import VideoJob, VideoJobBatch
from . import media_tools

_SORA_SECONDS = (4, 8, 12)  # the only durations OpenAI's Sora endpoint accepts


class VideoResult(BaseModel):
    """Outcome of one VideoJob."""

    job_id: Optional[str] = None
    shot_id: str
    segment_id: Optional[str] = None
    video_id: Optional[str] = Field(None, description="Remote video id returned by the backend")
    status: str = Field("pending", description="completed | failed | timeout")
    video_path: Optional[str] = Field(None, description="Local mp4 path when completed")
    error: Optional[str] = None
    generation_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class VideoClient:
    """
    Usage:
        client = VideoClient()                       # reads VIDEO_* from Config / .env
        result = client.generate(job, output_dir)    # submit + wait + download
        results = client.generate_batch(batch, run_root / "videos")
    """

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        poll_interval: Optional[float] = None,
        timeout: Optional[float] = None,
    ):
        from openai import OpenAI

        self.model = model or Config.VIDEO_MODEL
        self.base_url = base_url or Config.VIDEO_BASE_URL
        self.poll_interval = poll_interval or Config.VIDEO_POLL_INTERVAL
        self.timeout = timeout or Config.VIDEO_TIMEOUT
        self._client = OpenAI(api_key=api_key or Config.VIDEO_API_KEY or "EMPTY", base_url=self.base_url)
        print(f"   VideoClient initialized: model={self.model}, base_url={self.base_url or '<openai default>'}")

    # ── low-level: the three OpenAI Videos calls ─────────────────────────────

    def submit(self, job: VideoJob) -> str:
        """POST /videos — returns the remote video id (non-blocking)."""
        model = job.model or self.model
        seconds = max(1, int(round(job.duration)))
        if model.lower().startswith("sora"):
            seconds = min(_SORA_SECONDS, key=lambda s: abs(s - job.duration))
        extra_body: Dict[str, Any] = {
            "negative_prompt": job.negative_prompt,
            "fps": job.fps,
            "frame_num": job.frame_num,
            "duration": job.duration,
        }
        if job.seed is not None:
            extra_body["seed"] = job.seed
        if job.dialogue:  # joint audio-video backends can voice the line themselves
            extra_body.update({"dialogue": job.dialogue, "voice": job.voice, "voice_instructions": job.voice_instructions})
        extra_body.update(job.extra)

        kwargs: Dict[str, Any] = dict(
            model=model,
            prompt=job.prompt,
            size=job.size,
            seconds=str(seconds),
            extra_body=extra_body,
        )
        if job.image_reference:
            ref = Path(job.image_reference)
            if not ref.exists():
                raise FileNotFoundError(f"image_reference not found: {ref}")
            with open(ref, "rb") as f:
                kwargs["input_reference"] = f
                video = self._client.videos.create(**kwargs)
        else:
            video = self._client.videos.create(**kwargs)
        return video.id

    def wait(self, video_id: str):
        """GET /videos/{id} until status is terminal. Returns the final video object."""
        deadline = time.monotonic() + self.timeout
        while True:
            video = self._client.videos.retrieve(video_id)
            status = getattr(video, "status", "")
            if status in ("completed", "failed"):
                return video
            if time.monotonic() > deadline:
                raise TimeoutError(f"video {video_id} still {status!r} after {self.timeout:.0f}s")
            time.sleep(self.poll_interval)

    def download(self, video_id: str, path: Path) -> Path:
        """GET /videos/{id}/content — writes the mp4 to `path`."""
        path.parent.mkdir(parents=True, exist_ok=True)
        content = self._client.videos.download_content(video_id)
        content.write_to_file(str(path))
        return path

    def sample_frames(self, video_id: Optional[str], video_path: Path, out_dir: Path, n: int = 4) -> List[Path]:
        """
        Frames for the VLM judge. Prefers the backend's spritesheet (OpenAI Videos API
        `variant="spritesheet"`, one contact-sheet image); falls back to `ffmpeg`
        sampling `n` frames evenly. Returns [] when neither is available.
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(video_path).stem
        if video_id:
            try:
                sheet = out_dir / f"{stem}_sprites.jpg"
                self._client.videos.download_content(video_id, variant="spritesheet").write_to_file(str(sheet))
                if sheet.stat().st_size > 0:
                    return [sheet]
            except Exception:
                pass  # backend has no spritesheet -> ffmpeg
        return media_tools.sample_frames(Path(video_path), out_dir / stem, n)

    # ── high-level: one job / one batch ──────────────────────────────────────

    def generate(self, job: VideoJob, output_dir: Path) -> VideoResult:
        """Submit, wait, download. Never raises for a failed generation — see `status`/`error`."""
        name = job.job_id or f"{job.shot_id}_{job.segment_id or 'a'}"
        result = VideoResult(job_id=job.job_id, shot_id=job.shot_id, segment_id=job.segment_id)
        print(f"   🎬 [{name}] {'I2V' if job.image_reference else 'T2V'} {job.size} {job.duration:.1f}s", flush=True)
        try:
            result.video_id = self.submit(job)
            video = self.wait(result.video_id)
            if video.status != "completed":
                err = getattr(video, "error", None)
                result.status = "failed"
                result.error = getattr(err, "message", None) or str(err) or "generation failed"
                print(f"      ❌ {result.error}", flush=True)
                return result
            result.video_path = str(self.download(result.video_id, Path(output_dir) / f"{name}.mp4"))
            result.status = "completed"
            print(f"      ✅ {result.video_path}", flush=True)
        except TimeoutError as e:
            result.status, result.error = "timeout", str(e)
            print(f"      ⏱  {e}", flush=True)
        except Exception as e:  # network / auth / bad request
            result.status, result.error = "failed", f"{type(e).__name__}: {e}"
            print(f"      ❌ {result.error}", flush=True)
        return result

    def generate_batch(self, batch: VideoJobBatch, output_dir: Path) -> List[VideoResult]:
        """Run every job in order (sequential; keyframe-first chains rely on order)."""
        output_dir = Path(output_dir)
        results = [self.generate(job, output_dir) for job in batch.jobs]
        done = sum(1 for r in results if r.status == "completed")
        print(f"   VideoClient: {done}/{len(results)} clips completed", flush=True)
        return results
