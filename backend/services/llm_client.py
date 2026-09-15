"""
LLM Client Service — provider-agnostic LLM integration.

Uses httpx to call OpenAI-compatible chat completions endpoints so the
model/provider can be swapped via environment variables without rewriting
the AI orchestration layer.

Supported providers (OpenAI-compatible):
  - OPENAI_API_KEY         -> https://api.openai.com/v1/chat/completions
  - GROQ_API_KEY           -> https://api.groq.com/openai/v1/chat/completions
  - OPENROUTER_API_KEY     -> https://openrouter.ai/api/v1/chat/completions
  - LLM_BASE_URL + LLM_API_KEY  -> any custom/self-hosted endpoint
  - LLM_BASE_URL (no key)  -> local Ollama-style server

Environment variables:
  OPENAI_API_KEY        Primary API key (falls back to LLM_API_KEY)
  LLM_API_KEY           Alternative API key
  LLM_BASE_URL          Optional custom base URL (default OpenAI)
  LLM_MODEL             Optional model name override
  LLM_TIMEOUT_SECONDS   Optional request timeout (default 60)
"""

import json
import logging
import os
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger("llm_client")

DEFAULT_TIMEOUT = 60.0

# Default model per provider
PROVIDER_MODELS = {
    "openai": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "openai/gpt-4o-mini",
    "custom": os.environ.get("LLM_MODEL", "qwen2.5:7b"),
}


class LLMConfig:
    """Resolved LLM configuration from environment variables."""

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY") or ""
        self.base_url = os.environ.get("LLM_BASE_URL", "").rstrip("/")
        self.model = os.environ.get("LLM_MODEL", "")
        self.timeout = float(os.environ.get("LLM_TIMEOUT_SECONDS", DEFAULT_TIMEOUT))

        # Detect provider
        self.provider = self._detect_provider()

    def _detect_provider(self) -> str:
        if self.base_url:
            return "custom"
        if os.environ.get("GROQ_API_KEY"):
            return "groq"
        if os.environ.get("OPENROUTER_API_KEY"):
            return "openrouter"
        return "openai"

    @property
    def available(self) -> bool:
        # Local endpoints (e.g. Ollama) need no key
        if self.provider == "custom" and not self.api_key:
            return True
        return bool(self.api_key)

    @property
    def chat_url(self) -> str:
        if self.provider == "groq":
            return "https://api.groq.com/openai/v1/chat/completions"
        if self.provider == "openrouter":
            return "https://openrouter.ai/api/v1/chat/completions"
        if self.provider == "custom":
            return f"{self.base_url}/v1/chat/completions" if "v1" not in self.base_url else f"{self.base_url}/chat/completions"
        return "https://api.openai.com/v1/chat/completions"

    def _resolve_model(self) -> str:
        if self.model:
            return self.model
        return PROVIDER_MODELS.get(self.provider, PROVIDER_MODELS["openai"])


_cached_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    global _cached_config
    if _cached_config is None:
        _cached_config = LLMConfig()
    return _cached_config


def reset_llm_config():
    """Reset cached config (useful in tests)."""
    global _cached_config
    _cached_config = None


class LLMResponse:
    """Structured response from the LLM."""

    def __init__(self, content: str, model: str, provider: str, raw: Optional[Dict] = None):
        self.content = content
        self.model = model
        self.provider = provider
        self.raw = raw
        self.success = bool(content.strip())

    @property
    def usage(self) -> Optional[Dict]:
        if self.raw and isinstance(self.raw, dict):
            return self.raw.get("usage")
        return None


async def generate(
    system_prompt: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> LLMResponse:
    """
    Generate a completion via the configured provider.

    Args:
        system_prompt: System instructions for the LLM.
        messages: Conversation history (role/content pairs).
        temperature: Sampling temperature.
        max_tokens: Maximum output tokens.

    Returns:
        LLMResponse with content; success=False if generation failed.
    """
    config = get_llm_config()
    if not config.available:
        logger.warning("LLM not configured: no API key and no local LLM endpoint")
        return LLMResponse(content="", model=config.model, provider=config.provider)

    url = config.chat_url
    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    if config.provider == "openrouter":
        headers["HTTP-Referer"] = "https://agromind.ai"
        headers["X-Title"] = "AgroMind"

    payload = {
        "model": config._resolve_model(),
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        return LLMResponse(
            content=content,
            model=data.get("model", config._resolve_model()),
            provider=config.provider,
            raw=data,
        )
    except httpx.HTTPStatusError as e:
        logger.error("LLM HTTP error %s: %s", e.response.status_code, e.response.text[:500])
    except httpx.TimeoutException:
        logger.error("LLM request timed out after %.1fs", config.timeout)
    except Exception as e:
        logger.error("LLM request failed: %s", e)

    return LLMResponse(content="", model=config.model, provider=config.provider)


async def generate_cached(
    cache_key: str,
    system_prompt: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> LLMResponse:
    """
    Generate with a simple in-process cache to avoid duplicate expensive calls.
    """
    # In-memory LRU-ish cache (dict with no eviction for small footprint)
    global _llm_cache
    key = (cache_key, system_prompt[:200])
    if key in _llm_cache:
        import time
        age = time.time() - _llm_cache[key][0]
        if age < 3600:  # 1-hour TTL
            return _llm_cache[key][1]
        del _llm_cache[key]

    result = await generate(system_prompt, messages, temperature, max_tokens)

    if result.success:
        import time
        _llm_cache[key] = (time.time(), result)

    return result


_llm_cache: Dict[tuple, tuple] = {}


def llm_status() -> Dict:
    """Status of the LLM integration for health checks."""
    config = get_llm_config()
    return {
        "configured": config.available,
        "provider": config.provider if config.available else None,
        "model": config._resolve_model() if config.available else None,
        "endpoint": config.chat_url if config.available else None,
        "message": (
            "LLM ready via " + config.provider
            if config.available else
            "LLM not configured — set OPENAI_API_KEY, GROQ_API_KEY, "
            "OPENROUTER_API_KEY, or LLM_BASE_URL"
        ),
    }


if __name__ == "__main__":
    import asyncio
    print(llm_status())