#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
Agent Trace Logging — the reasoning layer (Trace Log), implemented as middleware.

- trace_id: the full lifecycle of one task/session (one trace_id per Pipeline run)
- span_id: a single LLM call or single execution step
- session_id: optional, the user-side session identifier

Config: configs/pipeline_settings.yaml -> pipeline.trace_log_dir / trace_logs_enabled;
the environment variable TRACE_LOGS=0 disables writing to disk.
"""

import functools
import os
import re
import time
import uuid
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar

# Project root (src/utils/agent_trace.py -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_trace_id_ctx: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_trace_dir_name_ctx: ContextVar[Optional[str]] = ContextVar("trace_dir_name", default=None)  # output dir name: date-time
_session_id_ctx: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
_span_counter_ctx: ContextVar[int] = ContextVar("span_counter", default=0)

# Span info already written under the current trace, used by index.md: (span_id, agent_name, fname, duration_sec)
# ContextVar does not support default_factory, so use default=None and read with _spans_ctx.get() or []
_spans_ctx: ContextVar[Optional[List[Dict[str, Any]]]] = ContextVar("spans", default=None)

# Optional: the trace output dir for this run (a logs dir alongside output). Once set, log_trace/write_index write here instead of using trace_log_dir + date-time.
_trace_output_dir_ctx: ContextVar[Optional[Path]] = ContextVar("trace_output_dir", default=None)

F = TypeVar("F", bound=Callable[..., Any])


def _load_trace_config() -> Dict[str, Any]:
    """Read trace-related config from configs/pipeline_settings.yaml."""
    cfg_path = _PROJECT_ROOT / "configs" / "pipeline_settings.yaml"
    if not cfg_path.exists():
        return {}
    try:
        import yaml
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("pipeline", {})
    except Exception:
        return {}


def set_trace_output_dir(path: Optional[Path]) -> None:
    """Set the trace output dir for this run (e.g. run_root/logs). Once set, logs and output live under the same run dir."""
    _trace_output_dir_ctx.set(path)


def get_trace_output_dir() -> Optional[Path]:
    """The trace dir specified for this run; returns None if unset."""
    return _trace_output_dir_ctx.get()


def get_trace_log_dir() -> Path:
    """The trace output root dir; prefers pipeline.trace_log_dir, otherwise defaults to data/logs."""
    cfg = _load_trace_config()
    raw = cfg.get("trace_log_dir") or os.environ.get("TRACE_LOG_DIR", "")
    if raw:
        p = Path(raw)
        if not p.is_absolute():
            p = _PROJECT_ROOT / p
        return p
    return _PROJECT_ROOT / "data" / "logs"


def _is_enabled() -> bool:
    """Whether trace writing to disk is enabled."""
    cfg = _load_trace_config()
    if "trace_logs_enabled" in cfg:
        if not cfg["trace_logs_enabled"]:
            return False
    return os.environ.get("TRACE_LOGS", "1") != "0"


def new_trace(session_id: Optional[str] = None) -> str:
    """
    Start a new Trace (usually called at the Pipeline entry point).
    The output dir name uses date-time: YYYY-MM-DD_HH-MM-SS; returns the trace_id.
    """
    trace_id = uuid.uuid4().hex[:16]
    dir_name = time.strftime("%Y-%m-%d_%H-%M-%S")
    _trace_id_ctx.set(trace_id)
    _trace_dir_name_ctx.set(dir_name)
    _session_id_ctx.set(session_id or trace_id)
    _span_counter_ctx.set(0)
    _spans_ctx.set([])
    return trace_id


def get_trace_id() -> Optional[str]:
    """The current Trace ID; returns None if unset."""
    return _trace_id_ctx.get()


def get_trace_dir_name() -> Optional[str]:
    """The current trace output dir name (date-time, e.g. 2026-02-04_03-03-24); falls back to trace_id if unset."""
    name = _trace_dir_name_ctx.get()
    if name:
        return name
    return get_trace_id()


def get_session_id() -> Optional[str]:
    return _session_id_ctx.get()


def next_span_id() -> str:
    """Generate the next Span ID under the current Trace (auto-incrementing for easy sorting)."""
    n = _span_counter_ctx.get()
    _span_counter_ctx.set(n + 1)
    return f"span_{n:04d}"


def _ensure_trace_id() -> str:
    """Automatically call new_trace if there is no trace_id yet."""
    tid = get_trace_id()
    if not tid:
        return new_trace()
    return tid


def _serialize_result(result: Any) -> str:
    """Convert a structured result into a readable string."""
    if result is None:
        return ""
    if hasattr(result, "model_dump_json"):
        return result.model_dump_json(indent=2, ensure_ascii=False)
    if hasattr(result, "model_dump"):
        import json
        return json.dumps(result.model_dump(), indent=2, ensure_ascii=False)
    return str(result)


def _register_span(span_id: str, agent_name: str, fname: str, duration_sec: float = 0) -> None:
    """Register a span under the current trace, used by write_index."""
    try:
        spans = _spans_ctx.get() or []
        spans.append({
            "span_id": span_id,
            "agent_name": agent_name,
            "fname": fname,
            "duration_sec": duration_sec,
        })
        _spans_ctx.set(spans)
    except LookupError:
        pass


def log_trace(
    agent_name: str,
    *,
    span_id: str,
    input_preview: str = "",
    prompt_rendered: str = "",
    raw_response: str = "",
    thought: str = "",
    validation: str = "Success",
    duration_sec: float = 0,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    token_usage: Optional[Dict[str, int]] = None,
    log_dir: Optional[Path] = None,
) -> None:
    """
    Write a Trace to {log_dir}/{trace_id}/{agent_name}_{span_id}.md.

    - metadata: e.g. model, temperature, system_fingerprint, to help diagnose model-side changes.
    - token_usage: e.g. {"prompt_tokens": N, "completion_tokens": M, "total_tokens": T}, for cost and monitoring.
    - thought: the model's intermediate reasoning (CoT / reasoning); recorded verbatim if present.
    """
    if not _is_enabled():
        return
    trace_id = _ensure_trace_id()
    override = get_trace_output_dir()
    if override is not None:
        dir_path = Path(override)
    else:
        base = log_dir or get_trace_log_dir()
        dir_path = base / get_trace_dir_name()
    dir_path.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in agent_name)
    fname = f"{safe_name}_{span_id}.md"
    file_path = dir_path / fname

    lines = [
        f"# Agent: {agent_name}",
        f"- **Span ID**: {span_id}",
        f"- **Trace ID**: {trace_id}",
        f"- **Session ID**: {get_session_id() or trace_id}",
        f"- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}",
        f"- **Duration**: {duration_sec:.2f}s",
        f"- **Validation**: {validation}",
        "",
    ]
    if metadata:
        lines.append("## Metadata\n")
        for k, v in metadata.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
    if token_usage:
        lines.append("## Token Usage (Cost Tracking)\n")
        lines.append(f"- **prompt_tokens**: {token_usage.get('prompt_tokens', 'N/A')}")
        lines.append(f"- **completion_tokens**: {token_usage.get('completion_tokens', 'N/A')}")
        lines.append(f"- **total_tokens**: {token_usage.get('total_tokens', 'N/A')}")
        lines.append("")
    if error:
        lines.append(f"- **Error**: {error}\n")
    if input_preview:
        lines.append("## Input (preview)\n")
        lines.append("```\n" + (input_preview[:2000] + "..." if len(input_preview) > 2000 else input_preview) + "\n```\n")
    if thought:
        lines.append("## Thought (Internal Monologue)\n")
        lines.append("```\n" + (thought[:10000] + "\n..." if len(thought) > 10000 else thought) + "\n```\n")
    if prompt_rendered:
        lines.append("## Prompt Rendered\n")
        lines.append("```\n" + (prompt_rendered[:8000] + "\n..." if len(prompt_rendered) > 8000 else prompt_rendered) + "\n```\n")
    if raw_response:
        lines.append("## Raw Response\n")
        lines.append("```json\n" + (raw_response[:12000] + "\n..." if len(raw_response) > 12000 else raw_response) + "\n```\n")

    try:
        file_path.write_text("\n".join(lines), encoding="utf-8")
        _register_span(span_id, agent_name, fname, duration_sec)
    except OSError:
        pass


def write_index(log_dir: Optional[Path] = None) -> None:
    """
    Generate index.md under the current trace dir: a summary table linking to all child Spans, forming mind-map-style navigation.
    Recommended to call at the end of the Pipeline.
    """
    if not _is_enabled():
        return
    trace_id = get_trace_id()
    override = get_trace_output_dir()
    if override is not None:
        dir_path = Path(override)
    else:
        dir_name = get_trace_dir_name()
        if not trace_id or not dir_name:
            return
        base = log_dir or get_trace_log_dir()
        dir_path = base / dir_name
    if not dir_path.exists():
        return

    try:
        raw = _spans_ctx.get()
        spans = list(raw) if raw else []
    except LookupError:
        spans = []
    # If not registered via log_trace, scan the directory to fill in
    if not spans:
        for f in sorted(dir_path.glob("*.md")):
            if f.name == "index.md":
                continue
            m = re.match(r"^(.+)_(span_\d+)\.md$", f.name)
            if m:
                spans.append({"agent_name": m.group(1), "span_id": m.group(2), "fname": f.name, "duration_sec": 0})
    if not spans:
        return

    lines = [
        f"# Trace: {trace_id}",
        f"- **Session ID**: {get_session_id() or trace_id}",
        f"- **Generated**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}",
        "",
        "## Spans (decision chain)",
        "",
        "| # | Span ID | Agent | File | Duration |",
        "|---|---------|-------|------|----------|",
    ]
    for i, s in enumerate(spans, 1):
        agent = s.get("agent_name", "—")
        span_id = s.get("span_id", "—")
        fname = s.get("fname", "")
        dur = s.get("duration_sec", 0)
        lines.append(f"| {i} | {span_id} | {agent} | [{fname}]({fname}) | {dur:.2f}s |")

    try:
        (dir_path / "index.md").write_text("\n".join(lines), encoding="utf-8")
    except OSError:
        pass


def trace_span(
    agent_name: Optional[str] = None,
    capture_return: bool = True,
) -> Callable[[F], F]:
    """
    Decorator: write a Trace for any function; a single @trace_span line auto-records input/output/duration/exceptions.

    - agent_name: if not passed, uses func.__module__ + func.__name__
    - capture_return: whether to serialize the return value into raw_response
    """

    def decorator(func: F) -> F:
        name = agent_name or f"{getattr(func, '__module__', '')}.{getattr(func, '__qualname__', func.__name__)}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _ensure_trace_id()
            span_id = next_span_id()
            input_preview = str(args)[:500] + str(kwargs)[:500]
            start = time.perf_counter()
            result = None
            err_msg = None
            validation = "Success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                validation = type(e).__name__
                err_msg = str(e)
                raise
            finally:
                duration = time.perf_counter() - start
                raw = _serialize_result(result) if capture_return and result is not None else ""
                log_trace(
                    agent_name=name,
                    span_id=span_id,
                    input_preview=input_preview,
                    raw_response=raw,
                    validation=validation,
                    duration_sec=duration,
                    error=err_msg,
                )

        return wrapper  # type: ignore[return-value]

    return decorator


def get_current_trace_dir() -> Optional[Path]:
    """The current trace's directory (the set_trace_output_dir dir if set, otherwise data/logs/<date-time>)."""
    override = get_trace_output_dir()
    if override is not None:
        return Path(override)
    dir_name = get_trace_dir_name()
    if not dir_name:
        return None
    return get_trace_log_dir() / dir_name
