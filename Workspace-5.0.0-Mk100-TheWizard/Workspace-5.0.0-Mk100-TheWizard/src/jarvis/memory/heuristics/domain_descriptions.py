"""Domain descriptions for UI tooltips and metadata.

Provides human-readable descriptions for all domains used in the Jarvis memory system.
"""

from __future__ import annotations

from typing import Dict

# Domain descriptions mapping: domain → human-readable description
# Used by /api/memory/domains/metadata endpoint to provide tooltip content
DOMAIN_DESCRIPTIONS: Dict[str, str] = {
    # === Jarvis System Domains ===
    "jarvis.core": "Core Jarvis system architecture, cognitive controller, and foundational components",
    "jarvis.api": "API layer, endpoints, and service interfaces",
    "jarvis.memory": "Memory systems, knowledge graphs, Qdrant integration, and retrieval",
    "jarvis.agents": "Agent coordination, multi-agent systems, and BMAD agent protocols",
    "jarvis.llm": "LLM providers, completions, and language model integrations",
    "jarvis.cognitive": "ARCHES cognitive architecture, reasoning, and decision-making systems",
    "jarvis.playbooks": "Operational playbooks, guides, and standard procedures",
    "jarvis.workflows": "BMAD workflows, automation, and process orchestration",

    # === Architecture Domains ===
    "architecture.core": "System architecture, design patterns, and architectural decisions",
    "architecture.data": "Data architecture, schemas, models, and persistence strategies",
    "architecture.integration": "Integration patterns, API contracts, and service boundaries",
    "architecture.deployment": "Deployment architecture, infrastructure, and operations",

    # === GenerativeDrive Energy Project Domains ===
    "gd.generativedrive": "GenerativeDrive project overview, vision, and strategic planning",
    "gd.partnerships": "Energy partnerships, stakeholder collaborations, and ecosystem connections",
    "gd.hydrogen": "Hydrogen economy systems, green hydrogen production, storage, and water loop",
    "gd.infra": "Telemetry, infrastructure monitoring, and operational systems for energy projects",
    "gd.solar": "Solar energy systems and photovoltaic infrastructure",
    "gd.wind": "Wind energy systems and eolic infrastructure",
    "gd.smart_grid": "Smart grid systems and intelligent energy distribution",
    "gd.sustainability": "Sustainability initiatives, circular economy, and environmental impact",

    # === Development & Testing Domains ===
    "dev.testing": "Test suites, testing strategies, and quality assurance",
    "dev.docs": "Developer documentation, API references, and guides",
    "dev.tools": "Development tools, utilities, and workflows",

    # === BMAD Domains ===
    "bmad.core": "BMAD Core methodology, principles, and framework",
    "bmad.workflows": "BMAD workflow specifications and execution patterns",
    "bmad.agents": "BMAD agent definitions and coordination protocols",
    "bmad.sprints": "Sprint planning, stories, epics, and execution tracking",
}


def get_domain_description(domain: str) -> str:
    """Get human-readable description for a domain.

    Args:
        domain: Domain name

    Returns:
        Description string, or default message if domain not found
    """
    return DOMAIN_DESCRIPTIONS.get(domain, f"Domain: {domain}")


def get_all_descriptions() -> Dict[str, str]:
    """Get all domain descriptions.

    Returns:
        Dictionary mapping domain names to descriptions
    """
    return DOMAIN_DESCRIPTIONS.copy()
