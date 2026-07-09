"""Domain heuristics for Jarvis knowledge cataloging.

This subpackage organizes domain classification heuristics by discipline
to maintain the taxonomy for a polymath's digital brain spanning:
- JARVIS system internals
- Cybersecurity & networking
- Banking & finance
- Psychology & neuroscience
- Philosophy
- Hard sciences (physics, chemistry, biology)
- AI & machine learning
- Enterprise consulting
- GenerativeDrive energy project
- Software development & infrastructure

Each module exports domain mappings that are aggregated by the parent
``domain_heuristics`` module.
"""

from __future__ import annotations

__all__ = [
    "ai_ml_domains",
    "cyber_domains",
    "enterprise_domains",
    "finance_domains",
    "gd_domains",
    "jarvis_domains",
    "philosophy_domains",
    "psychology_domains",
    "science_domains",
    "telecom_domains",
    "dev_infra_domains",
]
