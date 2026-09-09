"""Provider abstraction for the OpenBiz maturity engine."""

from dataclasses import dataclass
import os
import time
from typing import Any

from google import genai
from google.genai import types


class AIProviderError(RuntimeError):
    """Raised when a provider cannot be configured or return a response."""


@dataclass(frozen=True)
class AIResponse:
    provider: str
    model: str
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    request_id: str | None = None


def _is_retryable_error(error: Exception) -> bool:
    status_code = getattr(error, "status_code", None)
    if status_code in {408, 409, 429} or (isinstance(status_code, int) and status_code >= 500):
        return True
    return isinstance(error, (TimeoutError, ConnectionError))


class ResilientProvider:
    """Adds bounded retries and optional fallback to a provider."""

    def __init__(
        self,
        primary: Any,
        fallback: Any | None = None,
        max_retries: int | None = None,
        backoff_seconds: float | None = None,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.max_retries = max_retries if max_retries is not None else int(
            os.environ.get("AI_MAX_RETRIES", "2")
        )
        self.backoff_seconds = backoff_seconds if backoff_seconds is not None else float(
            os.environ.get("AI_RETRY_BACKOFF_SECONDS", "0.5")
        )

    def generate(self, **kwargs: Any) -> AIResponse:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return self.primary.generate(**kwargs)
            except Exception as error:
                last_error = error
                if not _is_retryable_error(error) or attempt == self.max_retries:
                    break
                if self.backoff_seconds > 0:
                    time.sleep(self.backoff_seconds * (attempt + 1))

        if self.fallback is not None and last_error is not None and _is_retryable_error(last_error):
            return self.fallback.generate(**kwargs)
        if last_error is not None:
            raise last_error
        raise AIProviderError("Nenhum provedor disponível para gerar a resposta.")


class GeminiProvider:
    """Gemini implementation of the shared provider contract."""

    provider_name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: Any | None = None,
    ) -> None:
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY")
        if client is None and not resolved_key:
            raise AIProviderError("GEMINI_API_KEY não configurada.")

        self.model = model or os.environ.get("AI_GEMINI_MODEL", "gemini-3.5-flash")
        self.client = client or genai.Client(api_key=resolved_key)

    def generate(
        self,
        contents: str,
        system_instruction: str,
        temperature: float = 0.3,
    ) -> AIResponse:
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
            ),
        )
        text = getattr(response, "text", None)
        if not text:
            raise AIProviderError("O Gemini retornou uma resposta sem texto.")

        usage = getattr(response, "usage_metadata", None)
        return AIResponse(
            provider=self.provider_name,
            model=self.model,
            text=text,
            input_tokens=getattr(usage, "prompt_token_count", None),
            output_tokens=getattr(usage, "candidates_token_count", None),
            request_id=getattr(response, "response_id", None),
        )


class AnthropicProvider:
    """Claude implementation of the shared provider contract."""

    provider_name = "claude"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: Any | None = None,
    ) -> None:
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if client is None and not resolved_key:
            raise AIProviderError("ANTHROPIC_API_KEY não configurada.")

        self.model = model or os.environ.get(
            "AI_CLAUDE_MODEL", "claude-sonnet-4-20250514"
        )
        if client is None:
            try:
                from anthropic import Anthropic
            except ImportError as error:
                raise AIProviderError(
                    "A dependência 'anthropic' não está instalada."
                ) from error
            client = Anthropic(api_key=resolved_key)
        self.client = client

    def generate(
        self,
        contents: str,
        system_instruction: str,
        temperature: float = 0.3,
    ) -> AIResponse:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=int(os.environ.get("AI_MAX_OUTPUT_TOKENS", "4096")),
            system=system_instruction,
            messages=[{"role": "user", "content": contents}],
            temperature=temperature,
        )
        text = "".join(
            block.text for block in getattr(response, "content", [])
            if getattr(block, "type", None) == "text"
        )
        if not text:
            raise AIProviderError("O Claude retornou uma resposta sem texto.")

        usage = getattr(response, "usage", None)
        return AIResponse(
            provider=self.provider_name,
            model=self.model,
            text=text,
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            request_id=getattr(response, "id", None),
        )


def create_provider(provider: str | None = None, **kwargs: Any) -> GeminiProvider | AnthropicProvider:
    """Create the configured provider from environment or an explicit name."""
    provider_name = (provider or os.environ.get("AI_PRIMARY_PROVIDER", "gemini")).lower()
    providers = {
        "gemini": GeminiProvider,
        "claude": AnthropicProvider,
    }
    provider_class = providers.get(provider_name)
    if provider_class is None:
        supported = ", ".join(sorted(providers))
        raise AIProviderError(
            f"Provedor '{provider_name}' inválido. Use: {supported}."
        )
    return provider_class(**kwargs)


def create_resilient_provider(provider: str | None = None, **kwargs: Any) -> ResilientProvider:
    """Create a provider with optional fallback, enabled explicitly by environment."""
    primary = create_provider(provider, **kwargs)
    fallback_name = os.environ.get("AI_FALLBACK_PROVIDER")
    fallback = None
    if os.environ.get("AI_FALLBACK_ENABLED", "false").lower() == "true" and fallback_name:
        fallback = create_provider(fallback_name)
    return ResilientProvider(primary=primary, fallback=fallback)
