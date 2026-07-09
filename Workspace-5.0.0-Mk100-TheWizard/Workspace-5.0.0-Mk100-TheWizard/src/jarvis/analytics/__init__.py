"""JARVIS analytics package."""

from jarvis.analytics.domain_evolution import (
    capture_domain_snapshot,
    capture_system_snapshot,
    get_domain_growth,
    get_top_growing_domains,
    get_evolution_timeline,
    format_domain_growth_report,
    DomainGrowth,
    create_snapshot_tables,
)

__all__ = [
    "capture_domain_snapshot",
    "capture_system_snapshot",
    "get_domain_growth",
    "get_top_growing_domains",
    "get_evolution_timeline",
    "format_domain_growth_report",
    "DomainGrowth",
    "create_snapshot_tables",
]
