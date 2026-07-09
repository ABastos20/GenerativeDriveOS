"""Tag descriptions for UI tooltips and metadata.

Provides human-readable descriptions for all tags used in the Jarvis memory system.
Includes both GenerativeDrive energy project tags and Jarvis system tags.
"""

from __future__ import annotations

from typing import Dict

# Tag descriptions mapping: tag → human-readable description
# Used by /api/memory/tags endpoint to provide tooltip content
TAG_DESCRIPTIONS: Dict[str, str] = {
    # === GenerativeDrive Energy Project Tags ===

    # Location
    "sines": "Sines region in Portugal, location of GenerativeDrive energy project",

    # Hydrogen economy
    "hydrogen": "Hydrogen production, storage, distribution, and infrastructure",
    "hydrogen_green": "Green hydrogen produced via renewable energy electrolysis",

    # Renewable energy sources
    "solar": "Solar energy systems, photovoltaic panels, and solar infrastructure",
    "wind": "Wind energy systems, wind farms, and eolic infrastructure",
    "hydro": "Hydroelectric power, dams, and water-based energy generation",
    "water": "Water systems, water resources, and water management",
    "renewable_energy": "General renewable and clean energy systems and policies",

    # Energy infrastructure
    "smart_grid": "Smart grid systems, intelligent energy distribution networks",
    "energy_storage": "Energy storage systems, batteries, and power storage solutions",

    # Sustainability
    "plastics": "Plastic materials, microplastics, and plastic waste management",
    "water_loops": "Closed water loop systems, water cycle management, circularity",

    # Technology
    "ai": "Artificial intelligence, machine learning, and LLM systems",

    # === Jarvis System Tags ===

    # Architecture & Design
    "architecture": "System architecture, design patterns, and architectural decisions",
    "cognitive": "Cognitive architecture, ARCHES controller, and reasoning systems",
    "memory": "Memory systems, knowledge graphs, Qdrant, and retrieval",
    "agents": "Agent systems, multi-agent coordination, and agent protocols",

    # Implementation
    "api": "API endpoints, REST interfaces, and service contracts",
    "database": "Database schemas, Postgres models, and data persistence",
    "llm": "Large language model integration, providers, and completions",
    "workflows": "BMAD workflows, automation, and process orchestration",

    # Features
    "grounding": "Context grounding, knowledge retrieval, and source attribution",
    "research": "Research mode, deep analysis, and comprehensive investigation",
    "conversation": "Conversation management, chat sessions, and dialogue state",
    "tracing": "Cognitive traces, observability, and reasoning transparency",

    # Development
    "testing": "Test suites, unit tests, integration tests, and QA",
    "deployment": "Deployment processes, Docker, and production operations",
    "performance": "Performance optimization, latency, and throughput",

    # Documentation
    "documentation": "Project documentation, guides, and reference materials",
    "bmad": "BMAD methodology, sprints, stories, and development practices",

    # Project-specific
    "generative_drive": "GenerativeDrive energy project overview and vision",
    "partnerships": "Energy partnerships, collaborations, and stakeholder relationships",
}


def get_tag_description(tag: str) -> str:
    """Get human-readable description for a tag.

    Args:
        tag: Tag name

    Returns:
        Description string, or default message if tag not found
    """
    return TAG_DESCRIPTIONS.get(tag, f"Tag: {tag}")


def get_all_descriptions() -> Dict[str, str]:
    """Get all tag descriptions.

    Returns:
        Dictionary mapping tag names to descriptions
    """
    return TAG_DESCRIPTIONS.copy()
