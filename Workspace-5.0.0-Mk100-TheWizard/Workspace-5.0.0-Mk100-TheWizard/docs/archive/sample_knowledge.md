# The Council of Ricks: A Multi-Agent System

## Overview
The Council of Ricks is a specialized multi-agent consensus system designed to provide diverse perspectives on complex queries. It leverages distinct personas to analyze problems from multiple angles before synthesizing a final answer.

## Personas
1.  **Rick Prime (The Nihilist)**: Focuses on raw facts, efficiency, and the cold hard truth. Disregards social niceties.
2.  **Doofus Rick (The Empathetic)**: Prioritizes emotional intelligence, user well-being, and ethical considerations.
3.  **Pickle Rick (The Survivalist)**: Emphasizes resourcefulness, improvisation, and high-risk/high-reward strategies.
4.  **Cop Rick (The Enforcer)**: Ensures compliance with rules, safety protocols, and structural integrity.

## Architecture
The system uses a parallel invocation model where the Orchestrator dispatches the user's query to all active personas simultaneously. Each persona generates a response based on its specific system prompt and context. The Aggregator then collects these responses and synthesizes a final "Consensus" answer, highlighting agreements and conflicts.

## Voting Mechanism
A weighted voting system is employed where each persona's confidence score contributes to the final decision. "Chaos Voting" allows for dynamic weight adjustments based on the query's domain (e.g., emotional queries boost Doofus Rick's weight).

# Jarvis System Architecture

## Core Components
-   **CLI**: The primary interface for interaction, built with Typer.
-   **Memory**: A hybrid storage system using Qdrant for vector search and PostgreSQL for structured metadata and full-text retrieval.
-   **LLM Gateway**: A unified interface for calling various LLM providers (OpenAI, Anthropic, Google, Local).

## Ingestion Pipeline
1.  **Ingest**: Documents are converted to Markdown, chunked, and embedded.
2.  **Catalog**: Chunks are classified into domains (e.g., "science", "philosophy").
3.  **Enrich**: An offline job adds summaries, facts, and tags to chunks to improve retrieval quality.
