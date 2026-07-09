"""Web search integration for autonomous research mode.

Uses Gemini with Google Search grounding for web research capabilities.
"""

from __future__ import annotations

import structlog
from typing import List
from jarvis.llm.providers import GoogleAIProvider

logger = structlog.get_logger(__name__)


def search_web(query: str, max_results: int = 5) -> List[str]:
    """Search the web using Gemini with Google Search grounding and return cited URLs.

    Args:
        query: Search query string
        max_results: Maximum number of URLs to return

    Returns:
        List of URLs found via Google Search grounding
    """
    try:
        logger.info("web_search_start", query=query, max_results=max_results, provider="gemini")

        # Use Gemini with Google Search grounding
        provider = GoogleAIProvider(model="gemini-2.5-pro")

        if not provider.is_available():
            logger.warning("gemini_not_available", message="Google AI API key not configured")
            return []

        response = provider.call(
            prompt=query,
            system="Search the web for this query. Provide factual, up-to-date information and cite your sources.",
            max_tokens=500,
            enable_search=True,  # Enable Google Search grounding
        )

        # Extract search URLs from grounding metadata
        search_urls = getattr(response, 'search_urls', []) if hasattr(response, '__dict__') else []
        urls = search_urls[:max_results]

        logger.info(
            "web_search_completed",
            query=query,
            urls_found=len(urls),
            urls=urls,
            provider="gemini",
        )

        return urls

    except Exception as exc:
        logger.error("web_search_failed", query=query, error=str(exc), provider="gemini")
        return []


def fetch_content_from_url(url: str) -> str:
    """Fetch and extract main content from a URL.

    Uses Gemini with Google Search grounding to analyze and summarize the URL content.

    Args:
        url: URL to fetch content from

    Returns:
        Extracted main content as text
    """
    try:
        logger.info("fetch_url_start", url=url, provider="gemini")

        provider = GoogleAIProvider(model="gemini-2.5-pro")

        if not provider.is_available():
            logger.warning("gemini_not_available", message="Google AI API key not configured")
            return ""

        # Use Gemini with grounding to analyze the URL
        response = provider.call(
            prompt=f"Summarize the key information from this URL: {url}\nExtract the most important facts and data.",
            system="You analyze web content and extract key information. Be concise and factual.",
            max_tokens=1000,
            enable_search=True,  # Enable Google Search to access the URL
        )

        content = response.content if hasattr(response, 'content') else ""

        logger.info("fetch_url_completed", url=url, content_length=len(content), provider="gemini")

        return content

    except Exception as exc:
        logger.error("fetch_url_failed", url=url, error=str(exc), provider="gemini")
        return ""
