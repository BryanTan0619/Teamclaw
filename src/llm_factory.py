"""
Factory helpers for creating the shared LangChain chat model instance.

This module supports provider-specific SDKs when available and falls back to
OpenAI-compatible routing for the rest. It also normalizes OpenAI base URLs so
users can provide either a root URL or a full endpoint URL.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

from langchain_core.language_models.chat_models import BaseChatModel


def extract_text(content) -> str:
    """Convert provider-specific message payloads into plain text."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)

    return str(content)


_MODEL_PROVIDER_PATTERNS: dict[str, str] = {
    "gemini": "google",
    "claude": "anthropic",
    "deepseek": "deepseek",
    "gpt": "openai",
    "o1": "openai",
    "o3": "openai",
    "o4": "openai",
    "qwen": "openai",
    "minimax": "openai",
    "glm": "openai",
    "moonshot": "openai",
    "yi-": "openai",
    "baichuan": "openai",
    "doubao": "openai",
    "hunyuan": "openai",
    "ernie": "openai",
    "mistral": "openai",
    "llama": "openai",
    "groq": "openai",
}

_NO_TEMPERATURE_PREFIXES = ("gpt-5", "o1", "o3", "o4")
_RESPONSES_API_PREFIXES = ("gpt-5", "o1", "o3", "o4")
_OPENAI_ENDPOINT_SUFFIXES = (
    "/v1/chat/completions",
    "/chat/completions",
    "/v1/responses",
    "/responses",
    "/v1/models",
    "/models",
)


def _model_has_prefix(model: str, prefix: str) -> bool:
    model_lower = model.lower()
    if not model_lower.startswith(prefix):
        return False

    return len(model_lower) == len(prefix) or model_lower[len(prefix)] in "-_."


def _model_supports_temperature(model: str) -> bool:
    return not any(_model_has_prefix(model, prefix) for prefix in _NO_TEMPERATURE_PREFIXES)


def _normalize_openai_base_url(base_url: str) -> str:
    cleaned = (base_url or "https://api.deepseek.com").strip().rstrip("/")
    cleaned_lower = cleaned.lower()

    for suffix in _OPENAI_ENDPOINT_SUFFIXES:
        if cleaned_lower.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            cleaned_lower = cleaned.lower()
            break

    if not cleaned_lower.endswith("/v1"):
        cleaned = cleaned.rstrip("/") + "/v1"

    return cleaned


def _is_native_openai_host(base_url: str) -> bool:
    parsed = urlparse(base_url)
    host = (parsed.netloc or parsed.path).lower()
    return host == "api.openai.com" or host.endswith(".openai.com")


def _should_use_responses_api(model: str, base_url: str) -> bool:
    return _is_native_openai_host(base_url) and any(
        _model_has_prefix(model, prefix) for prefix in _RESPONSES_API_PREFIXES
    )


def create_chat_model(
    *,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 60,
    max_retries: int = 2,
) -> BaseChatModel:
    """
    Create a chat model from TeamClaw environment variables.

    Required env vars:
      - LLM_API_KEY
      - LLM_MODEL
      - LLM_BASE_URL (optional for providers with hosted defaults)
    """
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").strip()
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()

    if not api_key:
        raise ValueError("LLM_API_KEY is not configured.")

    supports_temp = _model_supports_temperature(model)

    if not provider:
        model_lower = model.lower()
        for pattern, detected_provider in _MODEL_PROVIDER_PATTERNS.items():
            if pattern in model_lower:
                provider = detected_provider
                break
        else:
            provider = "openai"

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        kwargs = {
            "model": model,
            "google_api_key": api_key,
            "max_output_tokens": max_tokens,
            "timeout": timeout,
            "max_retries": max_retries,
        }
        if supports_temp:
            kwargs["temperature"] = temperature
        if base_url:
            kwargs["base_url"] = base_url
        return ChatGoogleGenerativeAI(**kwargs)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        kwargs = {
            "model": model,
            "api_key": api_key,
            "max_tokens": max_tokens,
            "timeout": timeout,
            "max_retries": max_retries,
        }
        if supports_temp:
            kwargs["temperature"] = temperature
        if base_url:
            kwargs["base_url"] = base_url
        return ChatAnthropic(**kwargs)

    if provider == "deepseek":
        from langchain_deepseek import ChatDeepSeek

        kwargs = {
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
            "max_tokens": max_tokens,
            "timeout": timeout,
            "max_retries": max_retries,
            "use_responses_api": False,
        }
        if supports_temp:
            kwargs["temperature"] = temperature
        return ChatDeepSeek(**kwargs)

    from langchain_openai import ChatOpenAI

    openai_base = _normalize_openai_base_url(base_url)
    kwargs = {
        "model": model,
        "base_url": openai_base,
        "api_key": api_key,
        "max_tokens": max_tokens,
        "timeout": timeout,
        "max_retries": max_retries,
    }
    if supports_temp:
        kwargs["temperature"] = temperature
    if _should_use_responses_api(model, openai_base):
        kwargs["use_responses_api"] = True

    return ChatOpenAI(**kwargs)
