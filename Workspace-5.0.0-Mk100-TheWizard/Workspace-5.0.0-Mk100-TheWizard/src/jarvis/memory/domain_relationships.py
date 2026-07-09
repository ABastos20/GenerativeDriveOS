"""Domain relationship graph for smarter retrieval.

This module defines semantic relationships between domains to enable
cross-domain retrieval expansion when primary domain searches fail.
"""

from __future__ import annotations

from typing import Dict, List, Set
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class DomainRelationship:
    """Relationship between two domains."""

    domain: str
    related_to: str
    relationship_type: str  # "child", "parent", "sibling", "cross_reference"
    strength: float  # 0.0-1.0, how strong the relationship is


# Domain relationship graph
# Format: domain -> {related_domain: (relationship_type, strength)}
DOMAIN_GRAPH: Dict[str, Dict[str, tuple[str, float]]] = {
    # JARVIS Memory relationships
    "jarvis.memory.rag": {
        "ai.embeddings": ("cross_reference", 0.9),  # RAG uses embeddings
        "ai.llm": ("cross_reference", 0.9),  # RAG uses LLMs
        "jarvis.memory": ("parent", 1.0),
        "jarvis.memory.ingestion": ("sibling", 0.7),
        "jarvis.memory.compilation": ("sibling", 0.7),
    },
    "jarvis.memory.ingestion": {
        "jarvis.memory": ("parent", 1.0),
        "jarvis.memory.rag": ("sibling", 0.7),
        "dev.python": ("cross_reference", 0.5),
    },
    "jarvis.memory.compilation": {
        "jarvis.memory": ("parent", 1.0),
        "jarvis.memory.rag": ("sibling", 0.7),
    },
    # JARVIS Agents
    "jarvis.agents": {
        "jarvis.personas": ("sibling", 0.8),
        "jarvis.llm": ("cross_reference", 0.7),
        "jarvis.workflows": ("cross_reference", 0.6),
    },
    "jarvis.personas": {
        "jarvis.agents": ("sibling", 0.8),
        "jarvis.config": ("cross_reference", 0.5),
    },
    # JARVIS LLM
    "jarvis.llm": {
        "ai.llm": ("cross_reference", 0.9),
        "jarvis.memory.rag": ("cross_reference", 0.8),
        "jarvis.agents": ("cross_reference", 0.7),
    },
    # JARVIS API/MCP
    "jarvis.api": {
        "jarvis.mcp": ("sibling", 0.9),
        "jarvis.cli": ("sibling", 0.7),
        "dev.fastapi": ("cross_reference", 0.8),
    },
    "jarvis.mcp": {
        "jarvis.api": ("sibling", 0.9),
        "jarvis.agents": ("cross_reference", 0.6),
    },
    # AI/ML relationships
    "ai.rag": {
        "ai.embeddings": ("cross_reference", 0.9),
        "ai.llm": ("cross_reference", 0.9),
        "ai.transformers": ("cross_reference", 0.7),
        "jarvis.memory.rag": ("cross_reference", 0.8),
    },
    "ai.embeddings": {
        "ai.rag": ("cross_reference", 0.9),
        "ai.transformers": ("cross_reference", 0.8),
        "math.linear_algebra": ("cross_reference", 0.6),
    },
    "ai.llm": {
        "ai.rag": ("cross_reference", 0.9),
        "ai.transformers": ("sibling", 0.8),
        "ai.prompt_engineering": ("sibling", 0.7),
    },
    # Cybersecurity relationships
    "cyber.stix": {
        "cyber.threat_intel": ("parent", 1.0),
        "cyber.mitre_attack": ("sibling", 0.8),
        "network.security": ("cross_reference", 0.7),
    },
    "cyber.pki": {
        "network.security": ("cross_reference", 0.8),
        "network.ssl_tls": ("cross_reference", 0.9),
        "math.cryptography": ("cross_reference", 0.7),
    },
    # Network/Telecom relationships
    "network.routing.bgp": {
        "network.routing": ("parent", 1.0),
        "network.routing.ospf": ("sibling", 0.7),
        "telecom.carrier": ("cross_reference", 0.6),
    },
    "network.telemetry": {
        "network.monitoring": ("sibling", 0.8),
        "telecom.nokia_sr_os": ("cross_reference", 0.7),
        "telecom.cisco": ("cross_reference", 0.7),
    },
    # Science relationships
    "science.physics.quantum": {
        "science.physics": ("parent", 1.0),
        "math.linear_algebra": ("cross_reference", 0.8),
        "math.complex_analysis": ("cross_reference", 0.7),
    },
    "science.neuroscience": {
        "psychology.cognitive": ("cross_reference", 0.9),
        "psychology.adhd": ("cross_reference", 0.7),
        "science.biology": ("parent", 0.8),
    },
    # Psychology relationships
    "psychology.adhd": {
        "psychology.executive_function": ("sibling", 0.9),
        "psychology.cognitive": ("cross_reference", 0.8),
        "science.neurology": ("cross_reference", 0.7),
    },
    "psychology.executive_function": {
        "psychology.adhd": ("sibling", 0.9),
        "psychology.cognitive": ("sibling", 0.8),
    },
    # Finance/Banking relationships
    "finance.banking.core": {
        "finance.banking": ("parent", 1.0),
        "finance.payments": ("sibling", 0.7),
        "enterprise.integration": ("cross_reference", 0.6),
    },
    "finance.trading": {
        "finance.risk": ("sibling", 0.8),
        "math.statistics": ("cross_reference", 0.7),
        "ai.ml": ("cross_reference", 0.6),
    },
    # Enterprise relationships
    "enterprise.togaf": {
        "enterprise.architecture": ("parent", 1.0),
        "enterprise.transformation": ("sibling", 0.7),
    },
    "enterprise.cloud.aws": {
        "enterprise.cloud": ("parent", 1.0),
        "enterprise.cloud.azure": ("sibling", 0.6),
        "enterprise.cloud.gcp": ("sibling", 0.6),
        "infra.cloud": ("cross_reference", 0.8),
    },
    # Dev/Infra relationships
    "dev.python": {
        "dev.fastapi": ("cross_reference", 0.7),
        "dev.django": ("sibling", 0.5),
        "infra.docker": ("cross_reference", 0.6),
    },
    "infra.docker": {
        "infra.kubernetes": ("sibling", 0.8),
        "infra.containers": ("parent", 1.0),
        "dev.devops": ("cross_reference", 0.7),
    },
    # BMAD relationships
    "bmad.workflows": {
        "bmad.method": ("parent", 1.0),
        "bmad.agents": ("sibling", 0.8),
        "jarvis.workflows": ("cross_reference", 0.7),
    },
    # GenerativeDrive project relationships
    "gd.generative_drive": {
        "gd.sines": ("child", 0.9),
        "gd.hydrogen": ("child", 0.9),
        "gd.solar": ("child", 0.8),
        "science.energy": ("cross_reference", 0.8),
    },
}


def get_related_domains(
    domain: str,
    max_depth: int = 2,
    min_strength: float = 0.5,
    include_types: List[str] | None = None,
) -> List[tuple[str, float]]:
    """Get related domains for retrieval expansion.

    Args:
        domain: Source domain
        max_depth: Maximum graph traversal depth
        min_strength: Minimum relationship strength to include
        include_types: Relationship types to include (None = all)

    Returns:
        List of (related_domain, combined_strength) tuples, sorted by strength
    """
    if include_types is None:
        include_types = ["parent", "child", "sibling", "cross_reference"]

    visited: Set[str] = {domain}
    results: Dict[str, float] = {}

    def traverse(current: str, depth: int, cumulative_strength: float):
        if depth > max_depth:
            return

        if current not in DOMAIN_GRAPH:
            return

        for related, (rel_type, strength) in DOMAIN_GRAPH[current].items():
            if rel_type not in include_types:
                continue

            if related in visited:
                continue

            # Calculate combined strength (decay with depth)
            combined = cumulative_strength * strength * (0.8 ** depth)

            if combined < min_strength:
                continue

            # Update best strength for this domain
            if related not in results or combined > results[related]:
                results[related] = combined

            visited.add(related)
            traverse(related, depth + 1, combined)

    # Start traversal
    traverse(domain, 0, 1.0)

    # Sort by strength descending
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

    return sorted_results


def expand_domain_filter(
    domains: List[str],
    max_expansions: int = 5,
    min_strength: float = 0.6,
) -> List[str]:
    """Expand a domain filter with related domains.

    Args:
        domains: Original domains to search
        max_expansions: Maximum additional domains to add
        min_strength: Minimum relationship strength

    Returns:
        Expanded domain list (original + related)
    """
    expanded = set(domains)
    related_candidates: Dict[str, float] = {}

    for domain in domains:
        related = get_related_domains(
            domain,
            max_depth=2,
            min_strength=min_strength,
        )

        for rel_domain, strength in related:
            if rel_domain not in expanded:
                # Keep highest strength if seen multiple times
                if rel_domain not in related_candidates or strength > related_candidates[rel_domain]:
                    related_candidates[rel_domain] = strength

    # Add top related domains
    sorted_related = sorted(
        related_candidates.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    for rel_domain, _ in sorted_related[:max_expansions]:
        expanded.add(rel_domain)

    logger.info(
        "domain_expansion",
        original_domains=domains,
        expanded_domains=list(expanded),
        added=len(expanded) - len(domains),
    )

    return list(expanded)


def get_domain_hierarchy(domain: str) -> Dict[str, List[str]]:
    """Get hierarchical view of domain relationships.

    Args:
        domain: Domain to analyze

    Returns:
        Dict with keys: parents, children, siblings, cross_refs
    """
    hierarchy = {
        "parents": [],
        "children": [],
        "siblings": [],
        "cross_references": [],
    }

    if domain not in DOMAIN_GRAPH:
        return hierarchy

    for related, (rel_type, strength) in DOMAIN_GRAPH[domain].items():
        if rel_type == "parent":
            hierarchy["parents"].append(related)
        elif rel_type == "child":
            hierarchy["children"].append(related)
        elif rel_type == "sibling":
            hierarchy["siblings"].append(related)
        elif rel_type == "cross_reference":
            hierarchy["cross_references"].append(related)

    return hierarchy


def visualize_domain_graph(domain: str, max_depth: int = 2) -> str:
    """Generate ASCII visualization of domain relationships.

    Args:
        domain: Root domain
        max_depth: Maximum depth to visualize

    Returns:
        ASCII graph string
    """
    lines = [f"Domain Relationship Graph: {domain}", "=" * 60, ""]

    def add_node(current: str, depth: int, prefix: str, is_last: bool):
        if depth > max_depth:
            return

        # Indent
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{current}")

        # Get relationships
        if current not in DOMAIN_GRAPH:
            return

        related = list(DOMAIN_GRAPH[current].items())

        for i, (rel_domain, (rel_type, strength)) in enumerate(related):
            is_last_child = i == len(related) - 1
            child_prefix = prefix + ("    " if is_last else "│   ")

            rel_label = f"{rel_domain} [{rel_type}, {strength:.1f}]"
            child_connector = "└── " if is_last_child else "├── "
            lines.append(f"{child_prefix}{child_connector}{rel_label}")

    add_node(domain, 0, "", True)

    return "\n".join(lines)
