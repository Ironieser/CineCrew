#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
"""
ConfigurableAgent: Generic configuration-driven LLM agent.

- Loads a YAML config supplied by the caller (each agent passes an absolute path
  to a YAML co-located in its own package, e.g. src/agents/<agent>/<name>.yaml)
- Compiles system/user prompts with Jinja2 (placeholders: {{ asset_context }}, {{ load_knowledge(...) }})
- Resolves output_schema to a Pydantic model and requests structured JSON
- Registers global skills (e.g. load_knowledge) in the Jinja environment
"""

import importlib
import time
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import jinja2

from ..utils import get_llm_client, generate_structured_data
from ..utils.types import LLMResult, TokenUsage
from ..utils.agent_trace import (
    _ensure_trace_id,
    log_trace,
    next_span_id,
    _serialize_result,
)
from ..config import Config


def _resolve_schema(schema_path: str) -> Type:
    """Resolve dotted path to a Pydantic model class."""
    module_path, _, class_name = schema_path.rpartition(".")
    if not module_path or not class_name:
        raise ValueError(f"Invalid output_schema path: {schema_path}")
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


def _describe_error(e: BaseException) -> str:
    """Error text for the trace: instructor wraps the real failure (429, timeout, schema) in
    InstructorRetryException('<failed_attempts>'), so walk the cause chain."""
    parts, seen = [], 0
    cur: Optional[BaseException] = e
    while cur is not None and seen < 5:
        text = str(cur).strip()
        if text and text != "<failed_attempts>":
            parts.append(f"{type(cur).__name__}: {text[:500]}")
        elif not parts:
            parts.append(type(cur).__name__)
        cur = cur.__cause__ or cur.__context__
        seen += 1
    return " <- ".join(parts)


def _default_globals() -> Dict[str, Any]:
    """Default Jinja2 globals (skills) available in all agent templates."""
    from ..skills.memory_loader import load_knowledge, load_module_specs
    return {"load_knowledge": load_knowledge, "load_module_specs": load_module_specs}


class ConfigurableAgent:
    """
    Generic agent that runs from a YAML config: prompts + output schema.
    """

    def __init__(
        self,
        config_path: str,
        jinja_globals: Dict[str, Any] | None = None,
    ):
        """
        Args:
            config_path: Path to the agent's YAML config. Agents pass an absolute
                path to a YAML co-located in their own package
                (e.g. str(Path(__file__).parent / "art_department.yaml")).
            jinja_globals: Extra functions/vars for Jinja (merged with load_knowledge, etc.)
        """
        path = Path(config_path)
        if not path.is_absolute():
            raise ValueError(
                "config_path must be absolute. Agents pass "
                "str(Path(__file__).parent / '<name>.yaml') so the YAML resolves "
                f"from the agent's own package; got relative path: {config_path!r}"
            )
        self._config_path = path

        with open(path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

        metadata = self._config.get("metadata", {})
        self._name = metadata.get("name", path.stem)
        # Optional: metadata.model in the YAML, or a top-level model, overrides Config.LLM_MODEL for this agent only
        self._model_override = metadata.get("model") or self._config.get("model")

        # Output schema: dotted path -> Pydantic model class
        schema_path = self._config.get("output_schema")
        if not schema_path:
            raise ValueError(f"Missing output_schema in {config_path}")
        self._output_schema = _resolve_schema(schema_path)

        # Jinja2: compile templates
        self._sys_template = jinja2.Template(self._config.get("system_prompt_template", ""))
        self._user_template = jinja2.Template(self._config.get("user_prompt_template", "{{ content }}"))

        # Globals: skills available in templates (e.g. load_knowledge)
        self.jinja_env_globals = {**_default_globals(), **(jinja_globals or {})}

        self._client = get_llm_client()

    def run(self, *, images: Optional[List[str]] = None, **kwargs: Any) -> Any:
        """
        Render prompts from kwargs and run the LLM; return a Pydantic instance.
        Automatically writes a Trace log to <run>/logs/{agent_name}_{span_id}.md.

        kwargs are passed to Jinja2 (e.g. script_segment, asset_context, hallucination_guard).
        `images`: local image paths attached to the user turn (vision models only).
        """
        _ensure_trace_id()
        span_id = next_span_id()
        render_context = {**self.jinja_env_globals, **kwargs}
        system_prompt = self._sys_template.render(**render_context)
        user_prompt = self._user_template.render(**render_context)
        prompt_rendered = f"=== System ===\n{system_prompt}\n\n=== User ===\n{user_prompt}"

        # Input preview: take the first 500 characters of script_excerpt / script_segment, etc.
        input_preview = ""
        for key in ("script_excerpt", "script_segment", "content", "script_segment_text"):
            if key in kwargs and isinstance(kwargs[key], str):
                input_preview = kwargs[key][:500]
                if len(kwargs[key]) > 500:
                    input_preview += "..."
                break

        start = time.perf_counter()
        result_content = None
        validation = "Success"
        err_msg = None
        token_usage: Optional[TokenUsage] = None
        try:
            llm_result: LLMResult = generate_structured_data(
                self._client,
                self._output_schema,
                system_prompt,
                user_prompt,
                model=self._model_override,
                images=images,
            )
            result_content = llm_result.content
            token_usage = llm_result.usage
            if result_content is None:
                raise ValueError("LLM returned empty content")
        except Exception as e:
            validation = type(e).__name__
            err_msg = _describe_error(e)
            raise
        finally:
            duration = time.perf_counter() - start
            raw_response = _serialize_result(result_content) if result_content is not None else ""
            metadata = {
                "model": self._model_override or Config.LLM_MODEL,
                "provider": Config.LLM_PROVIDER,
            }
            if images:
                metadata["images"] = ", ".join(Path(i).name for i in images)
            if Config.LLM_PROVIDER == "azure":
                metadata["api_version"] = Config.AZURE_API_VERSION
            log_trace(
                agent_name=self._name,
                span_id=span_id,
                input_preview=input_preview,
                prompt_rendered=prompt_rendered,
                raw_response=raw_response,
                validation=validation,
                duration_sec=duration,
                error=err_msg,
                metadata=metadata,
                token_usage=token_usage.to_dict() if token_usage else None,
            )

        return result_content

    @property
    def output_schema(self) -> Type:
        return self._output_schema

    @property
    def name(self) -> str:
        return self._name
