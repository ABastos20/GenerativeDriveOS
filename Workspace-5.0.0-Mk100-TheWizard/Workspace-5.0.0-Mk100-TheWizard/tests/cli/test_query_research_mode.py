from __future__ import annotations

import json
from types import SimpleNamespace

from typer.testing import CliRunner

from jarvis.cli.query import app as query_app
from jarvis import memory


def test_cli_query_enable_research_json(monkeypatch):
    runner = CliRunner()

    fake_results = [
        memory.search.SearchResult(
            text="irrelevant context",
            score=0.1,
            source_file="doc.md",
            section=None,
            domain="jarvis-core",
            metadata={},
        )
    ]

    monkeypatch.setattr(memory.search, "search_memory", lambda *a, **k: fake_results)
    monkeypatch.setattr(memory.search, "deduplicate_results", lambda r: r)
    monkeypatch.setattr(memory.search, "keyword_search", lambda *a, **k: fake_results)
    monkeypatch.setattr(memory.search, "hybrid_search", lambda *a, **k: fake_results)

    fake_llm_resp = SimpleNamespace(
        content="answer",
        input_tokens=1,
        output_tokens=1,
        provider="test",
        model="test-model",
        cost_usd=0.0,
    )
    monkeypatch.setattr("jarvis.cli.query.call_llm", lambda **kwargs: fake_llm_resp)
    import jarvis.llm.client as llm_client

    monkeypatch.setattr(llm_client, "call_llm", lambda **kwargs: fake_llm_resp)
    from jarvis.cli import query as query_mod

    monkeypatch.setattr(query_mod.ResearchPlanner, "plan", lambda self, q, g: SimpleNamespace(queries=[], gap_types=[], coverage_score=0.0, recency_status="STALE", coherence_score=0.0))
    monkeypatch.setattr(query_mod.MCPResearchExecutor, "execute", lambda self, plan: [])

    result = runner.invoke(
        query_app,
        [
            "coverage gap question",
            "--json-output",
            "--enable-research",
            "--k",
            "1",
        ],
    )

    assert result.exit_code == 0
    output = result.output
    json_start = output.find("{")
    payload = json.loads(output[json_start:])
    assert payload["metadata"]["research_enabled"] is True
    assert payload["metadata"]["research_summary"] is not None
    assert payload["metadata"]["gap_analysis"]["coverage_gap"] is True
