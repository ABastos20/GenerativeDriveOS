from __future__ import annotations

import json
from types import SimpleNamespace

from typer.testing import CliRunner

from jarvis.cli import analytics
from jarvis.database.models import ResearchLog


class _FakeQuery:
    def __init__(self, logs):
        self._logs = logs

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self._logs


class _FakeSession:
    def __init__(self, logs):
        self._logs = logs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, *args, **kwargs):
        return _FakeQuery(self._logs)


def _make_log(executed: int, sources: int, cost: float, gaps: dict | None = None) -> ResearchLog:
    log = SimpleNamespace()
    log.executed_queries = executed
    log.sources_collected = sources
    log.cost_usd = cost
    log.gap_types = gaps or {}
    log.created_at = None
    return log  # type: ignore[return-value]


def test_research_summary_cli_json(monkeypatch):
    logs = [
        _make_log(2, 3, 0.5, {"coverage_gap": True}),
        _make_log(1, 1, 0.2, {"recency_gap": True}),
    ]

    monkeypatch.setattr(analytics, "get_session", lambda: _FakeSession(logs))
    runner = CliRunner()
    result = runner.invoke(analytics.app, ["research-summary", "--json-output"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["sessions"] == 2
    assert payload["executed_queries"] == 3
    assert payload["sources_collected"] == 4
