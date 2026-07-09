"""Google AI SDK client - Separated for complexity compliance.

This module handles SDK-based calls to Google AI for standard (non-search) requests.
"""
from typing import Optional, Any
import structlog

from jarvis.llm.base import LLMResponse

logger = structlog.get_logger(__name__)


class GoogleAISDKClient:
    """SDK client for Google AI. Isolated from main provider for complexity."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-pro"):
        self.api_key = api_key
        self.model = model

    def call(self, prompt: str, system: Optional[str] = None, max_tokens: int = 4000) -> LLMResponse:
        """Execute SDK call to Google AI."""
        genai = self._configure_sdk()
        response = self._execute(genai, prompt, system, max_tokens)
        return self._process_response(response, prompt)

    def _configure_sdk(self) -> Any:
        """Configure Google GenAI SDK."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError("google-generativeai package not installed")
        genai.configure(api_key=self.api_key)
        return genai

    def _execute(self, genai: Any, prompt: str, system: Optional[str], max_tokens: int) -> Any:
        """Execute model call."""
        generation_config = genai.GenerationConfig(max_output_tokens=max_tokens)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        model_name = self.model.replace("models/", "")
        model = genai.GenerativeModel(model_name, system_instruction=system if system else None)
        return model.generate_content(prompt, generation_config=generation_config, safety_settings=safety_settings)

    def _process_response(self, response: Any, prompt: str) -> LLMResponse:
        """Process SDK response."""
        content = self._extract_text(response)
        input_tokens, output_tokens, cost_usd = self._calculate_cost(prompt, content)

        logger.warning(
            "llm_call_completed_PAID",
            provider="google-ai",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=round(cost_usd, 4),
            message="PAID API USED",
        )

        return LLMResponse(
            content=content,
            provider="google-ai",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )

    def _extract_text(self, response: Any) -> str:
        """Extract text from response."""
        try:
            return response.text
        except ValueError:
            pieces = []
            try:
                for cand in getattr(response, "candidates", []) or []:
                    content_obj = getattr(cand, "content", None)
                    for part in getattr(content_obj, "parts", []) or []:
                        text_piece = getattr(part, "text", None)
                        if text_piece:
                            pieces.append(text_piece)
            except Exception:
                pass
            return "".join(pieces)

    @staticmethod
    def _calculate_cost(prompt: str, content: str) -> tuple[int, int, float]:
        """Calculate token counts and cost."""
        input_tokens = len(prompt) // 4
        output_tokens = len(content) // 4
        cost_usd = (input_tokens * 0.075 / 1_000_000) + (output_tokens * 0.30 / 1_000_000)
        return input_tokens, output_tokens, cost_usd
