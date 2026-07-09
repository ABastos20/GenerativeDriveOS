"""MCP research execution orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Optional

from jarvis.memory.research_planner import ResearchPlan, ResearchQuery
from jarvis.memory.mcp_tools import fetch_url as default_fetch_url


@dataclass
class ResearchSource:
    url: str
    content: str
    quality: float
    query: str
    cross_ref_score: Optional[float] = None


@dataclass
class ResearchExecutionResult:
    query: str
    sources: List[ResearchSource]


class MCPResearchExecutor:
    """Execute research plan using MCP tools.

    The executor remains simple and injects tool callables for testability:
    - fetch_tool(url: str, prompt: str) -> dict with 'content'
    - search_tool(query: str) -> iterable of URLs (optional)
    - cross_ref(sources: list[ResearchSource]) -> list[ResearchSource] (optional post-processor)
    """

    def __init__(
        self,
        fetch_tool: Callable[[str, str], dict] = default_fetch_url,
        search_tool: Callable[[str], Iterable[str]] | None = None,
        cross_ref: Callable[[List[ResearchSource]], List[ResearchSource]] | None = None,
        max_sources_per_query: int = 3,
    ) -> None:
        self.fetch_tool = fetch_tool
        self.search_tool = search_tool
        self.cross_ref = cross_ref
        self.max_sources_per_query = max_sources_per_query

    def _quality_score(self, content: str) -> float:
        length = len(content.strip())
        if length <= 0:
            return 0.0
        # Simple heuristic: prefer moderate length snippets
        if length < 200:
            return 0.4
        if length < 2000:
            return 0.8
        return 0.6

    def _collect_urls(self, research_query: ResearchQuery) -> list[str]:
        if self.search_tool is None:
            return []
        urls: list[str] = []
        for url in self.search_tool(research_query.query):
            urls.append(url)
            if len(urls) >= self.max_sources_per_query:
                break
        return urls

    def execute(self, plan: ResearchPlan) -> list[ResearchExecutionResult]:
        results: list[ResearchExecutionResult] = []
        for query in plan.queries:
            urls = self._collect_urls(query)
            if not urls:
                # Without search tool, skip URL discovery and return empty
                results.append(ResearchExecutionResult(query=query.query, sources=[]))
                continue

            collected: list[ResearchSource] = []
            for url in urls:
                fetched = self.fetch_tool(url, prompt="Extract main content as markdown")
                content = fetched.get("content", "") if isinstance(fetched, dict) else ""
                quality = self._quality_score(content)
                collected.append(
                    ResearchSource(url=url, content=content, quality=quality, query=query.query)
                )
            if self.cross_ref:
                collected = self.cross_ref(collected)
            results.append(ResearchExecutionResult(query=query.query, sources=collected))
        return results
