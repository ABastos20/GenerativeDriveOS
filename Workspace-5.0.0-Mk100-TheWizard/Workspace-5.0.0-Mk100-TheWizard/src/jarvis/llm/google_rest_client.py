"""Google AI REST provider - Separated for complexity compliance.

This module handles REST API calls to Google AI, bypassing SDK limitations
for features like search grounding.
"""
from typing import Optional, Any
import httpx
import structlog

from jarvis.llm.providers import LLMResponse

logger = structlog.get_logger(__name__)


class GoogleAIRESTClient:
    """REST API client for Google AI. Isolated from main provider for complexity."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-pro", timeout: float = 120.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def call(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4000,
        enable_search: bool = False,
    ) -> LLMResponse:
        """Execute REST API call to Google AI."""
        payload = self._build_payload(prompt, system, max_tokens, enable_search)
        data = self._execute_request(payload)
        return self._process_response(data, prompt, enable_search)

    def _build_payload(
        self,
        prompt: str,
        system: Optional[str],
        max_tokens: int,
        enable_search: bool,
    ) -> dict:
        """Build REST API payload."""
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens},
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        if enable_search:
            payload["tools"] = [{"google_search": {}}]
        return payload

    def _execute_request(self, payload: dict) -> dict:
        """Execute HTTP request."""
        model_name = self.model.replace("models/", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                url,
                params={"key": self.api_key},
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code != 200:
                self._handle_error(response)
            return response.json()

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error response."""
        error_msg = response.text
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", response.text)
        except Exception:
            pass
        logger.error("google_ai_rest_error", status_code=response.status_code, error=error_msg)
        raise ValueError(f"Google AI API Error: {response.status_code} - {error_msg}")

    def _process_response(self, data: dict, prompt: str, enable_search: bool) -> LLMResponse:
        """Parse REST response into LLMResponse."""
        candidates = data.get("candidates", [])
        content = self._extract_content(candidates)
        input_tokens, output_tokens, cost_usd = self._calculate_cost(data, prompt, content)

        response_obj = LLMResponse(
            content=content,
            provider="google-ai",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )

        if enable_search and candidates:
            self._attach_grounding(response_obj, candidates)

        return response_obj

    @staticmethod
    def _extract_content(candidates: list) -> str:
        """Extract text content from candidates."""
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts if "text" in part)

    @staticmethod
    def _calculate_cost(data: dict, prompt: str, content: str) -> tuple[int, int, float]:
        """Calculate token counts and cost."""
        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", len(prompt) // 4)
        output_tokens = usage.get("candidatesTokenCount", len(content) // 4)
        cost_usd = (input_tokens * 0.075 / 1_000_000) + (output_tokens * 0.30 / 1_000_000)
        return input_tokens, output_tokens, cost_usd

    @staticmethod
    def _attach_grounding(response_obj: LLMResponse, candidates: list) -> None:
        """Attach grounding metadata to response."""
        grounding_metadata = candidates[0].get("groundingMetadata")
        if not grounding_metadata:
            return

        response_obj.__dict__['grounding_metadata'] = grounding_metadata
        search_urls = []
        for chunk in grounding_metadata.get('groundingChunks', []) or []:
            web = chunk.get('web')
            if web and web.get('uri'):
                search_urls.append(web['uri'])
        if search_urls:
            response_obj.__dict__['search_urls'] = search_urls
