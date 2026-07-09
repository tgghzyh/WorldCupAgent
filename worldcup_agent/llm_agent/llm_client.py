"""Small OpenAI-compatible chat client used by the LLM prediction agent."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class LLMClientError(RuntimeError):
    """Raised when an LLM request fails or returns invalid content."""


@dataclass
class ChatCompletionResult:
    content: str
    model: str
    provider: str


class OpenAICompatibleChatClient:
    """Minimal stdlib client for OpenAI-compatible chat completion APIs."""

    def __init__(
        self,
        *,
        provider: str,
        api_key: str,
        model: str,
        endpoint: str,
        timeout_seconds: int = 90,
        max_retries: int = 3,
        retry_base_seconds: float = 2.0,
    ) -> None:
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, max_retries)
        self.retry_base_seconds = max(0.0, retry_base_seconds)

    def chat(self, system_prompt: str, user_prompt: str) -> ChatCompletionResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.25,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        data = self._send_with_retries(request)

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMClientError(f"{self.provider} response missing message content") from exc

        return ChatCompletionResult(content=content, model=self.model, provider=self.provider)

    def _send_with_retries(self, request: urllib.request.Request) -> dict[str, Any]:
        retryable_statuses = {429, 500, 502, 503, 504}
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                last_error = LLMClientError(f"{self.provider} HTTP {exc.code}: {body[:500]}")
                if exc.code not in retryable_statuses or attempt >= self.max_retries:
                    raise last_error from exc
                self._sleep_before_retry(attempt)
            except urllib.error.URLError as exc:
                last_error = LLMClientError(f"{self.provider} request failed: {exc}")
                if attempt >= self.max_retries:
                    raise last_error from exc
                self._sleep_before_retry(attempt)
            except Exception as exc:
                raise LLMClientError(f"{self.provider} request failed: {exc}") from exc

        raise LLMClientError(f"{self.provider} request failed: {last_error}")

    def _sleep_before_retry(self, attempt: int) -> None:
        delay = self.retry_base_seconds * (2 ** attempt)
        if delay > 0:
            time.sleep(delay)


def create_chat_client() -> OpenAICompatibleChatClient | None:
    """Create a real LLM client from environment variables, or None if unavailable."""

    _load_local_env()

    if os.getenv("LLM_DISABLE", "").lower() in {"1", "true", "yes"}:
        return None

    generic_key = os.getenv("LLM_API_KEY")
    if generic_key:
        base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
        endpoint = os.getenv("LLM_CHAT_COMPLETIONS_URL") or _chat_endpoint_from_base_url(base_url)
        return OpenAICompatibleChatClient(
            provider=os.getenv("LLM_PROVIDER", "custom"),
            api_key=generic_key,
            model=os.getenv("LLM_MODEL", "xop35qwen2b"),
            endpoint=endpoint,
            timeout_seconds=_env_int("LLM_TIMEOUT_SECONDS", 90),
            max_retries=_env_int("LLM_MAX_RETRIES", 4),
            retry_base_seconds=_env_float("LLM_RETRY_BASE_SECONDS", 2.0),
        )

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return OpenAICompatibleChatClient(
            provider="openai",
            api_key=openai_key,
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            endpoint=os.getenv("OPENAI_CHAT_COMPLETIONS_URL", "https://api.openai.com/v1/chat/completions"),
            timeout_seconds=_env_int("LLM_TIMEOUT_SECONDS", 90),
            max_retries=_env_int("LLM_MAX_RETRIES", 4),
            retry_base_seconds=_env_float("LLM_RETRY_BASE_SECONDS", 2.0),
        )

    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    if dashscope_key:
        return OpenAICompatibleChatClient(
            provider="dashscope",
            api_key=dashscope_key,
            model=os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
            endpoint=os.getenv(
                "DASHSCOPE_CHAT_COMPLETIONS_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            ),
            timeout_seconds=_env_int("LLM_TIMEOUT_SECONDS", 90),
            max_retries=_env_int("LLM_MAX_RETRIES", 4),
            retry_base_seconds=_env_float("LLM_RETRY_BASE_SECONDS", 2.0),
        )

    return None


def _chat_endpoint_from_base_url(base_url: str) -> str:
    if not base_url:
        raise LLMClientError("LLM_BASE_URL is required when LLM_API_KEY is set")
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def _load_local_env() -> None:
    """Load simple KEY=value pairs from .env.local/.env without an extra dependency."""

    for path in (PROJECT_ROOT / ".env.local", PROJECT_ROOT / ".env"):
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


def parse_json_object(content: str) -> dict[str, Any]:
    """Parse a JSON object from an LLM message."""

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(content[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("LLM response must be a JSON object")
    return parsed
