"""LLM client for calling external language model APIs.

Provides a simple interface for LLM calls with cost tracking and error handling.
Supports multiple providers with automatic fallback.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import structlog

from jarvis.database.models import LLMProvider as DbLLMProvider
from jarvis.database.models import LLMUsageLog
from jarvis.database.postgres import DatabaseError, get_session
from jarvis.observability.metrics import llm_tokens_total
from jarvis.llm.providers import (
    AnthropicProvider,
    GoogleAIProvider,
    LLMProvider,
    LLMResponse as ProviderLLMResponse,
    LocalCLIProvider,
    OpenAIProvider,
    OpenRouterProvider,
    PerplexityProvider,
    ProviderRouter,
)

logger = structlog.get_logger(__name__)

# Re-export LLMResponse for backward compatibility
LLMResponse = ProviderLLMResponse


@dataclass
class LLMClient:
    """Simple LLM client for API calls.

    Routes to available providers via ProviderRouter; defaults to auto selection.
    """

    provider: str = "auto"
    model: str = "google/gemini-2.0-flash-exp:free"  # Preferred cheap/free default
    api_key: Optional[str] = None  # Optional override for providers that accept direct key
    timeout: float = 120.0

    def call(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Call the LLM API with the given prompt.

        Args:
            prompt: User message content
            system: Optional system message
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with content, provider, model, tokens, and cost

        Raises:
            httpx.HTTPError: If the API call fails
        """
        logger.info("llm_call_start", provider=self.provider, model=self.model, prompt_length=len(prompt))

        response = self._route_call(prompt, system=system, max_tokens=max_tokens)

        _log_llm_usage(response)

        return response

    def _route_call(self, prompt: str, system: Optional[str], max_tokens: int) -> LLMResponse:
        """Route the call to the selected provider(s)."""
        providers = self._build_providers()
        router = ProviderRouter(providers)
        return router.call(prompt=prompt, system=system, max_tokens=max_tokens)

    def _build_providers(self) -> list[LLMProvider]:
        """Build provider list based on selection."""
        if self.provider != "auto":
            return [self._provider_from_name(self.provider)]

        # Auto chain: prefer free/cheap first, then paid, then local CLI
        providers = [
            OpenRouterProvider(model=self.model, api_key=self.api_key, timeout=self.timeout),
            PerplexityProvider(model=self.model, api_key=self.api_key, timeout=self.timeout),
            GoogleAIProvider(model=self.model, api_key=self.api_key, timeout=self.timeout),
            AnthropicProvider(model=self.model, api_key=self.api_key, timeout=self.timeout),
            OpenAIProvider(model=self.model, api_key=self.api_key, timeout=self.timeout),
        ]

        # Skip LocalCLIProvider in Docker environments (no TTY)
        if not os.path.exists("/.dockerenv"):
            providers.append(LocalCLIProvider(model=self.model, timeout=self.timeout))

        return providers

    def _provider_from_name(self, name: str) -> LLMProvider:
        """Map provider name to implementation."""
        key = name.lower()
        if key in {"openrouter", "open-router"}:
            return OpenRouterProvider(model=self.model, api_key=self.api_key, timeout=self.timeout)
        if key in {"perplexity", "pplx"}:
            return PerplexityProvider(model=self.model, api_key=self.api_key, timeout=self.timeout)
        if key in {"anthropic", "claude"}:
            return AnthropicProvider(model=self.model, api_key=self.api_key, timeout=self.timeout)
        if key in {"google", "google-ai", "gemini"}:
            return GoogleAIProvider(model=self.model, api_key=self.api_key, timeout=self.timeout)
        if key in {"openai", "gpt"}:
            return OpenAIProvider(model=self.model, api_key=self.api_key, timeout=self.timeout)
        if key in {"local", "cli"}:
            return LocalCLIProvider(model=self.model, timeout=self.timeout)
        raise ValueError(f"Unknown provider '{name}'")


def _log_llm_usage(response: ProviderLLMResponse) -> None:
    """Best-effort logging of LLM usage into PostgreSQL.

    This should never raise; failures are logged and swallowed so that
    LLM calls remain robust even if the database is unavailable.
    """
    try:
        # 1. Custom Metrics (Prometheus)
        try:
            llm_tokens_total.add(
                int(response.input_tokens), 
                {"provider": response.provider, "model": response.model, "type": "input"}
            )
            llm_tokens_total.add(
                int(response.output_tokens), 
                {"provider": response.provider, "model": response.model, "type": "output"}
            )
        except Exception:
            pass  # Metrics failure shouldn't stop DB logging

        # 2. Database Logging (PostgreSQL)
        with get_session() as session:
            provider = (
                session.query(DbLLMProvider)
                .filter(DbLLMProvider.name == response.provider)
                .one_or_none()
            )

            if provider is None:
                # Default provider metadata; type/priority can be refined later.
                provider_type = "free_tier"
                if response.provider in {"anthropic", "google-ai", "openai"}:
                    provider_type = "paid"

                provider = DbLLMProvider(
                    name=response.provider,
                    type=provider_type,
                    priority=100,
                    tokens_used=0,
                    is_active=True,
                )
                session.add(provider)
                session.flush()  # ensure provider.id is populated

            usage = LLMUsageLog(
                provider_id=provider.id,
                message_id=None,
                model=response.model,
                tokens_input=int(response.input_tokens),
                tokens_output=int(response.output_tokens),
                cost_usd=Decimal(str(response.cost_usd)),
            )
            session.add(usage)

            logger.info(
                "llm_usage_logged",
                provider=response.provider,
                model=response.model,
                tokens_input=response.input_tokens,
                tokens_output=response.output_tokens,
                cost_usd=round(response.cost_usd, 6),
            )
    except DatabaseError as exc:
        logger.warning(
            "llm_usage_log_failed",
            error=str(exc),
            provider=response.provider,
            model=response.model,
        )
    except Exception as exc:
        # Defensive: never let logging failures break main LLM flow.
        logger.warning(
            "llm_usage_log_unexpected_error",
            error=str(exc),
            provider=response.provider,
            model=response.model,
        )


def call_llm(
    prompt: str,
    system: Optional[str] = None,
    provider: str = "auto",  # "auto" = smart routing with fallback
    model: str = "google/gemini-2.0-flash-exp:free",  # FREE MODEL (no cost, 50 req/day)
    max_tokens: int = 4000,
) -> LLMResponse:
    """Convenience function to call LLM with automatic provider fallback.

    Args:
        prompt: User message content
        system: Optional system message
        provider: LLM provider selection:
            FREE/CHEAP (Safe to use):
            - "auto": FREE/CHEAP ONLY (OpenRouter → Perplexity, protected)
            - "openrouter": OpenRouter free models (50 req/day per model) - FREE
            - "perplexity": Perplexity API (~$0.001 per request) - CHEAP

            EXPENSIVE (Direct APIs - use explicitly only!):
            - "anthropic": Anthropic Claude API (€ credits, ~$0.03/req) - EXPENSIVE!
            - "google-ai": Google AI Studio API (€250 credits, ~$0.01/req) - EXPENSIVE!
            - "openai": OpenAI API (€10 credits, ~$0.02/req) - EXPENSIVE!

            CLI TOOLS (Also use your credits):
            - "local-claude": Claude CLI (uses Anthropic credits)
            - "local-gemini": Gemini CLI (uses Google credits)
            - "local-codex": OpenAI CLI (uses OpenAI credits)
        model: Model identifier (for OpenRouter)
        max_tokens: Maximum tokens to generate

    Returns:
        LLMResponse with content, provider, model, tokens, and cost

    Examples:
        # Auto-routing with fallback (recommended)
        response = call_llm("Explain RAG systems")

        # Use specific local CLI
        response = call_llm("Fix this code", provider="local-claude")
    """
    # Canonical Provider Priority Order (Dec 2025)
    # Source of truth for economic/epistemic priority
    LLM_PROVIDER_PRIORITY = [
        # Tier 0 — Free / Seat CLIs
        "codex",        # OpenAI seat (volatile)
        "claude",       # Anthropic seat (stable)
        # "gemini",     # TODO: Future feature
        # "local-llm",  # TODO: Future feature (Ollama/LM Studio)
        
        # Tier 1 — Aggregators
        "openrouter",
        "perplexity",
        
        # Tier 2 — Direct APIs
        "google-api",
        "openai-api",
        "anthropic-api",
    ]
    
    if provider == "auto":
        # Tier 0: Seat CLIs (FREE) → Tier 1: Aggregators → Tier 2: APIs
        
        providers = [
            # Tier 0 — Free Seat CLIs (codex & claude only for now)
            LocalCLIProvider("codex"),   # OpenAI Codex CLI
            LocalCLIProvider("claude"),  # Anthropic Claude CLI
            
            # Tier 1 — Aggregators
            OpenRouterProvider(model=model),
            PerplexityProvider(),
            
            # Tier 2 — Direct APIs (last resort)
            GoogleAIProvider(),
            OpenAIProvider(),
            AnthropicProvider(),
        ]

        router = ProviderRouter(providers=providers)
        response = router.call(prompt, system=system, max_tokens=max_tokens)
        _log_llm_usage(response)
        return response

    elif provider == "openrouter":
        client = OpenRouterProvider(model=model)
        response = client.call(prompt, system=system, max_tokens=max_tokens)
        _log_llm_usage(response)
        return response

    elif provider == "perplexity":
        # Use default Perplexity model (don't pass OpenRouter model)
        client = PerplexityProvider()
        response = client.call(prompt, system=system, max_tokens=max_tokens)
        _log_llm_usage(response)
        return response

    elif provider == "anthropic":
        # Direct Anthropic Claude API (EXPENSIVE - uses your credits!)
        client = AnthropicProvider(model=model)
        response = client.call(prompt, system=system, max_tokens=max_tokens)
        _log_llm_usage(response)
        return response

    elif provider == "google-ai" or provider == "gemini":
        # Direct Google AI Studio API (uses your Google AI credits)
        # Default to 2.5-pro if no model specified, otherwise use requested model
        google_model = model or "gemini-2.5-pro"
        client = GoogleAIProvider(model=google_model)
        response = client.call(prompt, system=system, max_tokens=max_tokens)
        _log_llm_usage(response)
        return response

    elif provider == "openai":
        # Direct OpenAI API (EXPENSIVE - uses your €10 credits!)
        client = OpenAIProvider(model=model)
        response = client.call(prompt, system=system, max_tokens=max_tokens)
        _log_llm_usage(response)
        return response

    elif provider.startswith("local-"):
        cli_name = provider.replace("local-", "")
        client = LocalCLIProvider(cli_name)
        response = client.call(prompt, system=system, max_tokens=max_tokens)
        _log_llm_usage(response)
        return response

    else:
        # Legacy: fallback to old LLMClient for backward compatibility
        client = LLMClient(provider=provider, model=model)
        response = client.call(prompt, system=system, max_tokens=max_tokens)
        # LLMClient.call already logs usage via _log_llm_usage.
        return response
