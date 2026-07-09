"""Lightweight MCP tool adapters for research mode.

These helpers intentionally degrade gracefully: if MCP is not available, they
return empty content to allow upstream logic to continue without hard failures.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


def _fetch_via_http(url: str) -> dict:
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return {"content": resp.text}


def fetch_url(url: str, prompt: str | None = None) -> dict:
    """Fetch URL content via MCP docker fetch tool when configured, fallback to HTTP.

    Controlled by env var: JARVIS_USE_MCP_FETCH (default: true). If the MCP
    tool invocation fails, falls back to direct HTTP GET.
    """
    del prompt  # parity with MCP signature
    use_mcp = os.getenv("JARVIS_USE_MCP_FETCH", "1").lower() in {"1", "true", "yes"}
    if use_mcp:
        try:
            # Placeholder: real MCP call would be wired here; when integrated, replace
            # the HTTP fallback with mcp__MCP_DOCKER__fetch invocation.
            return _fetch_via_http(url)
        except Exception as exc:  # pragma: no cover - MCP/HTTP fallback path
            logger.warning("mcp_fetch_failed", url=url, error=str(exc))
    try:
        return _fetch_via_http(url)
    except Exception as exc:  # pragma: no cover - network/availability dependent
        logger.warning("http_fetch_failed", url=url, error=str(exc))
        return {"content": ""}


def browser_snapshot(url: str) -> dict:
    """Placeholder for MCP browser snapshot; currently returns empty snapshot."""
    logger.info("mcp_browser_snapshot_placeholder", url=url)
    return {"content": "", "url": url}


def browser_navigate(url: str) -> dict:
    """Placeholder for MCP browser navigation."""
    logger.info("mcp_browser_navigate_placeholder", url=url)
    return {"status": "ok", "url": url}


def browser_take_screenshot(url: str, filename: str | None = None) -> dict:
    """Placeholder for MCP browser screenshot."""
    logger.info("mcp_browser_screenshot_placeholder", url=url, filename=filename)
    return {"status": "ok", "path": filename or "screenshot.png"}
