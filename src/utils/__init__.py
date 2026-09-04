# Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation
# Paper: ECCV 2026
# Copyright (c) 2026 Sixun Dong
# Author: Sixun Dong
# Licensed under the Apache License, Version 2.0
# LLM utilities
import base64
import mimetypes
import time
from pathlib import Path
from typing import List, Optional

import instructor
from openai import AzureOpenAI, OpenAI
from ..config import Config
from .types import LLMResult, TokenUsage


def get_llm_client():
    """
    Build the structured-output LLM client.

    Default is a plain OpenAI-compatible client (`LLM_BASE_URL` + `LLM_API_KEY`), so
    OpenAI, vLLM, Ollama, LiteLLM, etc. all work. Set `LLM_PROVIDER=azure` for Azure
    OpenAI (then `LLM_BASE_URL` is the resource endpoint and `LLM_MODEL` the deployment).
    `instructor` in JSON mode turns Pydantic schemas into validated responses.
    """
    if not Config.LLM_API_KEY:
        raise RuntimeError(
            "No LLM API key configured. Set LLM_API_KEY (or OPENAI_API_KEY) in your "
            "environment or in a .env file at the project root — see .env.example."
        )
    # openai-level retries cover connection errors / timeouts with backoff;
    # instructor-level retries (generate_structured_data) cover invalid JSON.
    common = dict(api_key=Config.LLM_API_KEY, timeout=Config.LLM_TIMEOUT, max_retries=Config.LLM_MAX_RETRIES)
    if Config.LLM_PROVIDER == "azure":
        client = AzureOpenAI(api_version=Config.AZURE_API_VERSION, azure_endpoint=Config.LLM_BASE_URL, **common)
    else:
        client = OpenAI(base_url=Config.LLM_BASE_URL, **common)
    return instructor.from_openai(client, mode=instructor.Mode.JSON)


def _usage_from_completion(completion) -> TokenUsage:
    """Explicitly extract Usage from the OpenAI Completion object, without relying on monkey patching."""
    usage = TokenUsage()
    if not getattr(completion, "usage", None):
        return usage
    u = completion.usage
    usage.prompt_tokens = getattr(u, "prompt_tokens", 0) or 0
    usage.completion_tokens = getattr(u, "completion_tokens", 0) or 0
    usage.total_tokens = getattr(u, "total_tokens", 0) or 0
    details = getattr(u, "prompt_tokens_details", None)
    if details:
        usage.cache_hit_tokens = getattr(details, "cached_tokens", 0) or 0
    return usage


def _image_part(path: str) -> dict:
    """Encode a local image as an OpenAI `image_url` content part (data URI)."""
    p = Path(path)
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}


def generate_structured_data(
    client,
    model_class,
    system_prompt: str,
    user_content: str,
    model: Optional[str] = None,
    images: Optional[List[str]] = None,
):
    """
    Generic generation function that explicitly returns the LLMResult[T] envelope.
    NO FALLBACK: on validation failure, raise ValidationError directly.

    `images`: optional local image paths appended to the user turn (vision models),
    used by the VLM visual judge.
    """
    start = time.perf_counter()
    if images:
        user_msg = {"role": "user", "content": [{"type": "text", "text": user_content}, *map(_image_part, images)]}
    else:
        user_msg = {"role": "user", "content": user_content}
    messages = [{"role": "system", "content": system_prompt}, user_msg]
    kwargs = dict(
        response_model=model_class,
        messages=messages,
        model=model or Config.LLM_MODEL,
        max_retries=Config.LLM_MAX_RETRIES,
        max_completion_tokens=Config.LLM_MAX_COMPLETION_TOKENS,
    )
    # Prefer create_with_completion to obtain both content and the raw completion (instructor >= 1.0)
    if hasattr(client, "create_with_completion"):
        content, raw = client.create_with_completion(**kwargs)
        usage = _usage_from_completion(raw)
        return LLMResult(content=content, usage=usage, latency=time.perf_counter() - start, raw_response=raw)
    content = client.chat.completions.create(**kwargs)
    return LLMResult(
        content=content,
        usage=TokenUsage(),
        latency=time.perf_counter() - start,
        raw_response=None,
    )

