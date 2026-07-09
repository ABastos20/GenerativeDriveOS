"""JARVIS system domain mappings.

Covers Jarvis' internal architecture, subsystems, and operational domains.
This is the self-awareness layer - how Jarvis understands itself.
"""

from __future__ import annotations

from typing import Dict

# Direct domain mappings for JARVIS subsystems
JARVIS_DIRECT_DOMAIN_MAP: Dict[str, str] = {
    # Legacy/raw payload values
    "jarvis-core": "jarvis.core",
    "jarvis-conversations": "jarvis.conversations",
    "jarvis-insights": "jarvis.insights",
    "jarvis-memory": "jarvis.memory",
    "jarvis-agents": "jarvis.agents",
}

# Keyword-based classification for JARVIS components
JARVIS_KEYWORD_MAP: Dict[str, str] = {
    # Core system
    "jarvis core": "jarvis.core",
    "jarvis system": "jarvis.core",
    "jarvis architecture": "jarvis.architecture",

    # Memory & RAG
    "jarvis memory": "jarvis.memory",
    "jarvis rag": "jarvis.memory.rag",
    "retrieval augmented": "jarvis.memory.rag",
    "hybrid retrieval": "jarvis.memory.rag",
    "semantic search": "jarvis.memory.rag",
    "query expansion": "jarvis.memory.rag",
    "reciprocal rank fusion": "jarvis.memory.rag",
    "rrf ": "jarvis.memory.rag",
    "document ingestion": "jarvis.memory.ingestion",
    "chunk ingestion": "jarvis.memory.ingestion",
    "embedding generation": "jarvis.memory.ingestion",
    "qdrant collection": "jarvis.memory",
    "vector database": "jarvis.memory",
    "knowledge compilation": "jarvis.memory.compilation",

    # Agents & Personas
    "council of ricks": "jarvis.agents",
    "rickiest rick": "jarvis.personas",
    "supportive rick": "jarvis.personas",
    "empathetic rick": "jarvis.personas",
    "analytical rick": "jarvis.personas",
    "persona registry": "jarvis.personas",
    "persona config": "jarvis.personas",
    "weighted voting": "jarvis.personas",
    "multi-agent reasoning": "jarvis.agents",
    "agent orchestration": "jarvis.agents",

    # LLM & Providers
    "llm provider": "jarvis.llm",
    "provider fallback": "jarvis.llm",
    "openrouter": "jarvis.llm",
    "perplexity": "jarvis.llm",
    "google gemini": "jarvis.llm",
    "anthropic claude": "jarvis.llm",
    "local claude": "jarvis.llm",
    "cost protection": "jarvis.llm",

    # API & Interfaces
    "jarvis api": "jarvis.api",
    "fastapi": "jarvis.api",
    "rest api": "jarvis.api",
    "jarvis mcp": "jarvis.mcp",
    "mcp server": "jarvis.mcp",
    "model context protocol": "jarvis.mcp",

    # CLI
    "jarvis cli": "jarvis.cli",
    "typer command": "jarvis.cli",
    "jarvis query": "jarvis.cli",
    "jarvis ingest": "jarvis.cli",

    # Database
    "jarvis database": "jarvis.database",
    "postgres schema": "jarvis.database",
    "alembic migration": "jarvis.database",
    "conversation storage": "jarvis.database",

    # Configuration
    "jarvis config": "jarvis.config",
    "settings.py": "jarvis.config",
    "environment variables": "jarvis.config",
    "secret management": "jarvis.config",

    # Workflows & Integration
    "jarvis workflow": "jarvis.workflows",
    "bmad integration": "jarvis.workflows",
    "jarvis playbook": "jarvis.playbooks",
    "operating manual": "jarvis.playbooks",

    # Conversations & History
    "jarvis conversation": "jarvis.conversations",
    "gpt export": "jarvis.gpt_export",
    "gpt conversation": "jarvis.gpt_export",
    "conversation export": "jarvis.gpt_export",
    "user snapshot": "jarvis.user_snapshot",

    # Analytics & Observability
    "jarvis analytics": "jarvis.insights",
    "citation provenance": "jarvis.insights",
    "citation analytics": "jarvis.insights",
    "conversation analytics": "jarvis.insights",
    "usage statistics": "jarvis.insights",
    "jarvis telemetry": "jarvis.insights",
}
