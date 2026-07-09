"""LLM provider abstraction for multiple backends.

Supports (Nov 2025):
FREE/CHEAP:
- OpenRouter API (free models: 50 req/day per model, 10+ models available)
- Perplexity API (sonar models: ~$0.001 per request)

PAID APIs (use explicitly only):
- Anthropic Claude API (direct API, uses your credits)
- Google AI Studio API (Gemini, uses your €250 credits)
- OpenAI API (GPT-4o, uses your €10 credits)

CLI TOOLS (use your API keys):
- Local CLI tools (claude, gemini, codex wrappers)
"""

from __future__ import annotations

import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def call(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Call the LLM provider with the given prompt."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available (credentials, CLI installed, etc)."""
        pass


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider (free and paid models)."""

    def __init__(
        self,
        model: str = "google/gemini-2.0-flash-exp:free",
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: float = 120.0,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = base_url
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if OpenRouter API key is configured."""
        return bool(self.api_key)

    def call(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Call OpenRouter API."""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/anthropics/jarvis",  # Required by OpenRouter
            "X-Title": "JARVIS RAG System",  # Optional but recommended
        }

        logger.info(
            "llm_call_start",
            provider="openrouter",
            model=self.model,
            prompt_length=len(prompt),
        )

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        cost_usd = float(data.get("cost", 0.0))

        logger.info(
            "llm_call_completed",
            provider="openrouter",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=round(cost_usd, 4),
        )

        return LLMResponse(
            content=content,
            provider="openrouter",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )


class PerplexityProvider(LLMProvider):
    """Perplexity API provider (defaults to offline models to avoid forced web search)."""

    def __init__(
        self,
        model: str = "sonar",  # Default to Sonar (online) but we will disable search
        api_key: Optional[str] = None,
        base_url: str = "https://api.perplexity.ai",
        timeout: float = 120.0,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        self.base_url = base_url
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if Perplexity API key is configured."""
        return bool(self.api_key)

    def call(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Call Perplexity API."""
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not configured")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "disable_search": True,  # Explicitly disable web search for RAG pipelines
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(
            "llm_call_start",
            provider="perplexity",
            model=self.model,
            prompt_length=len(prompt),
        )

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        # Perplexity pricing: ~$0.001 per 1K tokens (estimate)
        cost_usd = (input_tokens + output_tokens) * 0.001 / 1000

        # Extract citations if available (Perplexity sonar returns web sources)
        citations = data.get("citations", [])
        if citations:
            logger.info(
                "perplexity_citations_found",
                count=len(citations),
                urls=[c for c in citations if isinstance(c, str)],
            )

        logger.info(
            "llm_call_completed",
            provider="perplexity",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=round(cost_usd, 4),
        )

        response_obj = LLMResponse(
            content=content,
            provider="perplexity",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
        # Attach citations as metadata for research mode
        if citations and hasattr(response_obj, '__dict__'):
            response_obj.__dict__['citations'] = citations

        return response_obj


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider (direct API, uses your credits)."""

    def __init__(
        self,
        model: str = "claude-opus-4.5",  # Nov 2025: Latest Opus model
        api_key: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.model = model
        # Use Jarvis-specific env alias so we don't conflict with
        # npm CLI tools that may also look at ANTHROPIC_API_KEY.
        self.api_key = api_key or os.environ.get("JARVIS_ANTHROPIC_API_KEY")
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(self.api_key)

    def call(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Call Anthropic Claude API."""
        if not self.api_key:
            raise ValueError("JARVIS_ANTHROPIC_API_KEY not configured")

        try:
            from anthropic import Anthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

        client = Anthropic(api_key=self.api_key)

        messages = [{"role": "user", "content": prompt}]

        logger.warning(
            "llm_call_start_PAID",
            provider="anthropic",
            model=self.model,
            prompt_length=len(prompt),
            message="⚠️ USING PAID ANTHROPIC API - This uses your credits!",
        )

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
            system=system if system else None,
        )

        content = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # Claude pricing (Nov 2025): Claude Opus 4.5
        # Input: $3 per 1M tokens, Output: $15 per 1M tokens (estimated)
        cost_usd = (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000)

        logger.warning(
            "llm_call_completed_PAID",
            provider="anthropic",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=round(cost_usd, 4),
            message="⚠️ PAID API USED",
        )

        return LLMResponse(
            content=content,
            provider="anthropic",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )


class GoogleAIProvider(LLMProvider):
    """Google AI Studio API provider (uses your €250 credits)."""

    def __init__(
        self,
        model: str = "gemini-2.5-pro",  # Dec 2024: Gemini 2.5 Pro
        api_key: Optional[str] = None,
        timeout: float = 120.0,
    ):
        # Sanitize model name: if it's an OpenRouter ID, use default Gemini model
        if "/" in model:  # OpenRouter format: "google/gemini-2.0-flash-exp:free"
            self.model = "gemini-2.5-pro"
        else:
            self.model = model
        # Use Jarvis-specific env aliases to avoid colliding with
        # npm CLIs that may also read GOOGLE_* variables.
        self.api_key = api_key or os.environ.get("JARVIS_GOOGLE_API_KEY") or os.environ.get(
            "JARVIS_GOOGLE_GENAI_API_KEY"
        )
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if Google AI API key is configured."""
        return bool(self.api_key)

    def _execute_sdk_call(self, prompt: str, system: Optional[str], max_tokens: int) -> LLMResponse:
        """Delegate SDK calls to external client (class split for complexity)."""
        from jarvis.llm.google_sdk_client import GoogleAISDKClient
        client = GoogleAISDKClient(self.api_key, self.model)
        return client.call(prompt, system, max_tokens)

    def _call_rest(
        self,
        prompt: str,
        system: Optional[str],
        max_tokens: int,
        enable_search: bool,
    ) -> LLMResponse:
        """Delegate REST calls to external client (class split for complexity)."""
        from jarvis.llm.google_rest_client import GoogleAIRESTClient
        client = GoogleAIRESTClient(self.api_key, self.model, self.timeout)
        return client.call(prompt, system, max_tokens, enable_search)


    def call(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Call Google AI API (REST by default)."""
        if not self.is_available():
            raise ValueError("JARVIS_GOOGLE_API_KEY not configured")
            
        return self._call_rest(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            enable_search=False,
        )

class OpenAIProvider(LLMProvider):
    """OpenAI API provider (uses your €10 credits)."""

    def __init__(
        self,
        model: str = "gpt-5.1",  # Nov 2025: Latest GPT model
        api_key: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.model = model
        # Use Jarvis-specific env alias so we don't conflict with
        # npm CLIs that may also look at OPENAI_API_KEY.
        self.api_key = api_key or os.environ.get("JARVIS_OPENAI_API_KEY")
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.api_key)

    def call(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Call OpenAI API."""
        if not self.api_key:
            raise ValueError("JARVIS_OPENAI_API_KEY not configured")

        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        client = OpenAI(api_key=self.api_key)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        logger.warning(
            "llm_call_start_PAID",
            provider="openai",
            model=self.model,
            prompt_length=len(prompt),
            message="⚠️ USING PAID OPENAI API - This uses your €10 credits!",
        )

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        # GPT-5.1 pricing (Nov 2025): $2.50 per 1M input, $10 per 1M output (estimated)
        cost_usd = (input_tokens * 2.50 / 1_000_000) + (output_tokens * 10.0 / 1_000_000)

        logger.warning(
            "llm_call_completed_PAID",
            provider="openai",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=round(cost_usd, 4),
            message="⚠️ PAID API USED",
        )

        return LLMResponse(
            content=content,
            provider="openai",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )


class LocalCLIProvider(LLMProvider):
    """Local CLI tool provider (claude, gemini, codex)."""

    def __init__(self, cli_name: str, model_name: Optional[str] = None):
        self.cli_name = cli_name
        self.model_name = model_name or cli_name

    def is_available(self) -> bool:
        """Check if CLI tool is installed and accessible."""
        try:
            result = subprocess.run(
                [self.cli_name, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def call(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Call local CLI tool."""
        import tempfile
        import json
        import re
        from uuid import uuid4
        
        logger.info(
            "llm_call_start",
            provider=f"local-{self.cli_name}",
            model=self.model_name,
            prompt_length=len(prompt),
        )

        # Build CLI command based on tool
        output_file = None
        if self.cli_name == "codex":
            # Codex needs file-based output to avoid JSONL streaming hang
            output_file = f"/tmp/codex_{uuid4().hex}.json"
        
        cmd = self._build_command(prompt, system, max_tokens, output_file=output_file)

        # Prepare environment for CLI
        env = os.environ.copy()
        env["CI"] = "true"  # Hint for some tools to be non-interactive
        env["NO_COLOR"] = "true"  # Disable colors

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,  # Don't raise on non-zero exit (some CLIs return non-zero on success)
                stdin=subprocess.DEVNULL,
                env=env,
            )
            
            # Extract content based on provider type
            if self.cli_name == "codex" and output_file:
                # Read from file for Codex
                try:
                    with open(output_file) as f:
                        content = f.read().strip()
                    os.remove(output_file)  # Clean up
                except FileNotFoundError:
                    # Fallback to stdout if file wasn't created
                    content = result.stdout.strip()
                    
            elif self.cli_name == "claude":
                # Parse Claude JSON wrapper to extract actual result
                try:
                    wrapper = json.loads(result.stdout)
                    raw_result = wrapper.get("result", "")
                    # Strip markdown code fences if present
                    raw_result = re.sub(r'^```json\s*', '', raw_result)
                    raw_result = re.sub(r'\s*```$', '', raw_result)
                    content = raw_result.strip()
                except (json.JSONDecodeError, KeyError):
                    content = result.stdout.strip()
            else:
                content = result.stdout.strip()

            # Estimate tokens (rough approximation: 1 token ≈ 4 chars)
            input_tokens = len(prompt) // 4
            output_tokens = len(content) // 4

            logger.info(
                "llm_call_completed",
                provider=f"local-{self.cli_name}",
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=0.0,
            )

            return LLMResponse(
                content=content,
                provider=f"local-{self.cli_name}",
                model=self.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=0.0,  # Local CLI = free
            )

        except subprocess.TimeoutExpired as exc:
            logger.error(
                "llm_call_timeout",
                provider=f"local-{self.cli_name}",
                error="CLI timeout after 120s",
            )
            raise RuntimeError(f"CLI timeout: {self.cli_name}") from exc
        except subprocess.CalledProcessError as exc:
            logger.error(
                "llm_call_failed",
                provider=f"local-{self.cli_name}",
                error=str(exc),
                stderr=exc.stderr,
            )
            raise RuntimeError(f"CLI call failed: {exc.stderr}") from exc

    def _build_command(
        self, prompt: str, system: Optional[str], max_tokens: int, output_file: Optional[str] = None
    ) -> list[str]:
        """Build CLI command based on tool.
        
        LOCK 5: Prompt & Tool Sovereignty
        All CLI invocations are constrained to NARRATIVE MODE ONLY.
        This prevents codex/claude from entering developer mode.
        """
        # LOCK 5: Narrative Mode Preamble (prevents developer mode activation)
        NARRATIVE_MODE_PREAMBLE = """NARRATIVE MODE ONLY.
You may NOT:
- Suggest code changes or edits
- Generate file modifications
- Propose shell commands or scripts
- Describe implementation steps
- Enter developer or coding mode

You MAY:
- Analyze context and synthesize information
- Generate narrative, story, or analytical text
- Reason about governance and institutional dynamics
- Provide structured responses in JSON format

"""
        # For official CLIs, embed system prompt into the main prompt
        # instead of relying on CLI-specific system flags.
        combined_prompt = (
            f"{system}\n\n{prompt}" if system else prompt
        )
        
        # JSON wrapper for combined prompt
        json_prompt = f"Return ONLY valid JSON. No markdown. No commentary.\n\n{combined_prompt}"
        
        # Apply narrative mode preamble for agent-facing CLIs (Lock 5)
        safe_json_prompt = f"{NARRATIVE_MODE_PREAMBLE}{json_prompt}"

        # Claude CLI - use -p (print) mode with JSON output
        if self.cli_name == "claude":
            return [
                "claude", "-p",  # Non-interactive print mode
                "--output-format", "json",  # JSON output
                safe_json_prompt  # LOCK 5: Safe prompt with preamble
            ]

        # Gemini CLI (assuming similar interface)
        if self.cli_name in ("gemini", "google-gemini"):
            return ["gemini", safe_json_prompt]

        # Codex CLI - use 'exec' with --output-last-message for clean JSON
        if self.cli_name == "codex":
            cmd = [
                "codex", "exec",
                "--skip-git-repo-check",
                "--color", "never",
            ]
            if output_file:
                cmd.extend(["--output-last-message", output_file])
            cmd.append(safe_json_prompt)  # LOCK 5: Safe prompt with preamble
            return cmd

        # Codex-CLI (Python wrapper - already JSON-only)
        if self.cli_name == "codex-cli":
            return ["codex-cli", safe_json_prompt]

        # Claude-CLI (Python wrapper)
        if self.cli_name == "claude-cli":
            return ["claude-cli", safe_json_prompt]

        # Gemini-CLI (Python wrapper)
        if self.cli_name == "gemini-cli":
            return ["gemini-cli", safe_json_prompt]

        # Generic fallback
        return [self.cli_name, combined_prompt]



class ProviderRouter:
    """Routes LLM calls to available providers with fallback."""

    def __init__(self, providers: list[LLMProvider]):
        self.providers = providers

    def call(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Try providers in order until one succeeds."""
        last_error = None

        for provider in self.providers:
            if not provider.is_available():
                logger.debug(
                    "provider_unavailable",
                    provider=provider.__class__.__name__,
                )
                continue

            try:
                return provider.call(prompt, system=system, max_tokens=max_tokens)
            except httpx.HTTPStatusError as exc:
                # Rate limit or other HTTP error - try next provider
                logger.warning(
                    "provider_failed_fallback",
                    provider=provider.__class__.__name__,
                    status_code=exc.response.status_code,
                    error=str(exc),
                )
                last_error = exc
                continue
            except Exception as exc:
                # Unexpected error - try next provider
                logger.error(
                    "provider_error",
                    provider=provider.__class__.__name__,
                    error=str(exc),
                )
                last_error = exc
                continue

        # All providers failed
        raise RuntimeError(
            f"All LLM providers failed. Last error: {last_error}"
        ) from last_error
