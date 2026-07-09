from __future__ import annotations

from typing import Any, List

from jarvis.cli.analytics import aggregate_citation_stats


def test_aggregate_citation_stats_by_source_file() -> None:
    """Aggregate citation stats by source_file."""
    provenance_values: List[Any] = [
        [
            {
                "id": 1,
                "source_file": "a.md",
                "section": "A1",
                "domain": "jarvis-core",
            },
            {
                "id": 2,
                "source_file": "b.md",
                "section": "B1",
                "domain": "jarvis-core",
            },
        ],
        [
            {
                "id": 3,
                "source_file": "a.md",
                "section": "A2",
                "domain": "jarvis-insights",
            }
        ],
        # Envelope-style value with sources[]
        {
            "sources": [
                {
                    "id": 4,
                    "source_file": "c.md",
                    "section": "C1",
                    "domain": "jarvis-core",
                }
            ]
        },
    ]

    stats = aggregate_citation_stats(provenance_values, group_by="source_file")

    assert stats["total_citations"] == 4
    assert stats["unique_values"] == 3

    top = stats["top"]
    # a.md should be first with count 2
    assert top[0]["value"] == "a.md"
    assert top[0]["count"] == 2


def test_aggregate_citation_stats_by_domain() -> None:
    """Aggregate citation stats by domain."""
    provenance_values: List[Any] = [
        [
            {"domain": "jarvis-core"},
            {"domain": "jarvis-core"},
        ],
        [
            {"domain": "jarvis-insights"},
        ],
    ]

    stats = aggregate_citation_stats(provenance_values, group_by="domain")

    assert stats["total_citations"] == 3
    assert stats["unique_values"] == 2

    top = stats["top"]
    assert top[0]["value"] == "jarvis-core"
    assert top[0]["count"] == 2

