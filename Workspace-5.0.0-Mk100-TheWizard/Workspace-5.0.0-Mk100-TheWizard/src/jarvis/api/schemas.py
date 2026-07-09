"""Pydantic schemas for API request/response models.

These schemas define the contract between the API and clients,
providing validation and serialization for all endpoints.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, confloat, conint


class JarvisModel(BaseModel):
    """Base Pydantic model with consistent config."""

    model_config = ConfigDict(arbitrary_types_allowed=True)


# --- Request Schemas ---


class CreateConversationRequest(JarvisModel):
    """Request model for creating a new conversation."""

    user_id: Optional[str] = Field(None, description="Optional user identifier")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_123"
            }
        }
    )


class CreateMessageRequest(JarvisModel):
    """Request model for adding a message to a conversation."""

    role: str = Field(..., description="Message role: user | assistant | system")
    content: str = Field(..., min_length=1, description="Message content")
    agent_persona: Optional[str] = Field(None, description="Agent persona (e.g., Rickiest Rick)")
    cost_usd: Optional[Decimal] = Field(None, description="Cost in USD")
    provider: Optional[str] = Field(None, description="LLM provider name")
    model: Optional[str] = Field(None, description="LLM model name")
    token_count: Optional[int] = Field(None, ge=0, description="Total tokens used")
    citation_provenance: Optional[List[dict[str, Any]]] = Field(
        None,
        description=(
            "Optional citation metadata for assistant messages; mirrors the sources[] JSON "
            "envelope (ids, files, sections, domains, scores, hashes, etc.)."
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "content": "Hello, JARVIS!",
                "agent_persona": None,
                "cost_usd": None,
                "provider": None,
                "model": None,
                "token_count": None,
                "citation_provenance": None,
            }
        }
    )


class MemorySearchRequest(JarvisModel):
    """Request model for semantic memory search."""

    query: str = Field(..., min_length=1, description="Natural language query string")
    persona: Optional[str] = Field(
        None,
        description="Optional persona hint (reserved for future use)",
    )
    source: Optional[str] = Field(
        None,
        description="Logical source/domain filter (e.g., 'jarvis-core', 'jarvis-conversations')",
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Optional list of tags to filter by (AND logic - chunks must have all tags)",
    )
    since: Optional[str] = Field(
        None,
        description="Optional time filter (e.g., '7d' or ISO-8601); currently parsed but unused",
    )
    k: conint(ge=1, le=50) = Field(  # type: ignore[valid-type]
        10,
        description="Number of results to return (1-50)",
    )


# --- Response Schemas ---


class ConversationResponse(JarvisModel):
    """Response model for conversation metadata."""

    id: UUID
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode for SQLAlchemy models
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user_123",
                "created_at": "2025-11-17T15:30:00Z",
                "updated_at": "2025-11-17T15:35:00Z"
            }
        },
    )


class MessageResponse(JarvisModel):
    """Response model for message data."""

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    agent_persona: Optional[str]
    cost_usd: Optional[Decimal]
    provider: Optional[str]
    model: Optional[str]
    token_count: Optional[int]
    citation_provenance: Optional[List[dict[str, Any]]] = Field(
        None,
        description=(
            "Optional citation metadata for assistant messages; mirrors the sources[] JSON "
            "envelope (ids, files, sections, domains, scores, hashes, etc.)."
        ),
    )
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "456e7890-e89b-12d3-a456-426614174111",
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "user",
                "content": "Hello, JARVIS!",
                "agent_persona": None,
                "cost_usd": None,
                "provider": None,
                "model": None,
                "token_count": None,
                "citation_provenance": None,
                "created_at": "2025-11-17T15:30:00Z"
            }
        },
    )


class ConversationWithMessagesResponse(JarvisModel):
    """Response model for conversation with paginated messages."""

    conversation: ConversationResponse
    messages: List[MessageResponse]
    total_messages: int
    page: int
    page_size: int
    has_more: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "user_123",
                    "created_at": "2025-11-17T15:30:00Z",
                    "updated_at": "2025-11-17T15:35:00Z"
                },
                "messages": [],
                "total_messages": 0,
                "page": 1,
                "page_size": 50,
                "has_more": False
            }
        }
    )


class CreateConversationResponse(JarvisModel):
    """Response model for newly created conversation."""

    id: UUID
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2025-11-17T15:30:00Z"
            }
        },
    )


class CreateMessageResponse(JarvisModel):
    """Response model for newly created message."""

    id: UUID
    conversation_id: UUID
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "456e7890-e89b-12d3-a456-426614174111",
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2025-11-17T15:30:00Z"
            }
        },
    )


class ConversationSummary(JarvisModel):
    """Lightweight summary for listing conversations."""

    id: UUID
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_message: Optional[str]
    last_message_at: Optional[datetime]
    message_count: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "web-ui",
                "created_at": "2025-11-17T15:30:00Z",
                "updated_at": "2025-11-17T16:00:00Z",
                "last_message": "What is the Jarvis knowledge pipeline?",
                "last_message_at": "2025-11-17T16:00:00Z",
                "message_count": 6,
            }
        }
    )


class MemorySearchResult(JarvisModel):
    """Single memory search hit."""

    text: str = Field(..., description="Snippet text")
    score: confloat(ge=0.0) = Field(..., description="Similarity score (higher is more similar)")  # type: ignore[valid-type]
    doc_id: Optional[str] = Field(
        None,
        description="Document identifier when available (for full-text fetch)",
    )
    doc_key: Optional[str] = Field(
        None,
        description="Document key/path when available",
    )
    source_file: Optional[str] = Field(
        None,
        description="Original source file path, if available",
    )
    section: Optional[str] = Field(
        None,
        description="Section or heading within the source file",
    )
    domain: Optional[str] = Field(
        None,
        description="Logical domain label (e.g., 'jarvis-core')",
    )
    metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Additional metadata payload stored with the point",
    )


class MemorySearchResponse(JarvisModel):
    """Response model for memory search."""

    results: List[MemorySearchResult]


class DocumentResponse(JarvisModel):
    """Full document content and metadata."""

    id: UUID
    doc_key: str
    source_file: str
    domain: Optional[str]
    content: str
    metadata: Optional[dict[str, Any]] = None


class DomainMetadata(JarvisModel):
    """Metadata for a single domain."""

    name: str = Field(..., description="Domain name")
    description: str = Field(..., description="Human-readable description")
    chunk_count: int = Field(..., description="Number of chunks in this domain")


class DomainListResponse(JarvisModel):
    """List of known domains in the knowledge base."""

    domains: List[str]


class DomainMetadataResponse(JarvisModel):
    """List of domains with metadata."""

    domains: List[DomainMetadata]


class TagMetadata(JarvisModel):
    """Metadata for a single tag."""

    tag: str = Field(..., description="Tag name")
    description: str = Field(..., description="Human-readable description")
    count: int = Field(..., description="Number of chunks with this tag")


class TagsListResponse(JarvisModel):
    """List of known tags in the knowledge base."""

    tags: List[str]


class TagMetadataResponse(JarvisModel):
    """List of tags with metadata."""

    tags: List[TagMetadata]


# --- Chat Schemas ---


class ChatRequest(JarvisModel):
    """Request model for chat-style RAG queries."""

    message: str = Field(..., min_length=1, description="User message / question")
    agent_persona: Optional[str] = Field(
        default=None, description="Optional agent persona tag for prompt conditioning"
    )
    conversation_id: Optional[UUID] = Field(
        None,
        description="Optional existing conversation ID to append messages to",
    )
    user_id: Optional[str] = Field(
        None,
        description="Optional user identifier for new conversations",
    )
    provider: str = Field(
        "auto",
        description="LLM provider selection (auto, openrouter, perplexity, etc.)",
    )
    source: Optional[str] = Field(
        None,
        description="Optional logical source/domain filter (e.g., 'jarvis-core')",
    )
    k: conint(ge=1, le=20) = Field(  # type: ignore[valid-type]
        10,
        description="Number of context chunks to retrieve (1-20)",
    )
    max_tokens: int = Field(
        2000,
        ge=1,
        le=4000,
        description="Maximum tokens to generate in the LLM response",
    )
    retriever: Optional[str] = Field(
        None,
        description="Retrieval mode: semantic | keyword | hybrid (defaults from settings.query)",
    )
    weight: Optional[float] = Field(
        None,
        description="Semantic weight for hybrid retriever (0.0-1.0); defaults from settings.query",
    )
    strict_mode: bool = Field(
        False,
        description="Enable strict mode (no hallucinations; answer only from context)",
    )
    expand: Optional[int] = Field(
        None,
        description="Query expansion count (0-5); if omitted, uses configuration defaults",
    )
    enable_research: bool = Field(
        False,
        description="Opt-in flag to run gap detection and, when enabled, trigger research mode.",
    )
    grounding_level: Optional[str] = Field(
        None,
        description="soft | balanced | strict. Controls how tightly answers must stick to retrieved sources. If not set and auto_grounding is enabled, Jarvis will auto-detect based on query intent.",
    )
    auto_grounding: bool = Field(
        True,
        description="Enable autonomous grounding level selection based on query intent analysis.",
    )
    show_confidence: bool = Field(
        False,
        description="Add in-line confidence tags to response showing evidence pedigree.",
    )

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "message": "How does the Jarvis knowledge pipeline work?",
                "conversation_id": None,
                "user_id": "web-ui",
                "provider": "auto",
                "source": "jarvis-core",
                "k": 10,
                "max_tokens": 2000,
                "retriever": "semantic",
                "weight": 0.7,
                "strict_mode": False,
                "expand": 0,
                "grounding_level": "balanced",
                "enable_research": False,
            }
        }
    )


class ChatSource(JarvisModel):
    """Single source chunk used to answer a chat message."""

    id: int = Field(..., description="Stable ordinal identifier for the source in this answer")
    content: str = Field(..., description="Snippet text used as context")
    doc_id: Optional[str] = Field(
        None,
        description="Document identifier when available (for fetching full content)",
    )
    doc_key: Optional[str] = Field(
        None,
        description="Document key/path when available",
    )
    source_file: Optional[str] = Field(
        None,
        description="Original source file path, if available",
    )
    section: Optional[str] = Field(
        None,
        description="Section or heading within the source file",
    )
    domain: Optional[str] = Field(
        None,
        description="Logical domain label (e.g., 'jarvis-core', 'bmad-insights')",
    )
    relevance_score: float = Field(
        ...,
        description="Original retrieval score from memory search",
    )
    score: float = Field(
        ...,
        description="Alias for relevance_score for downstream tools",
    )

    chunk_id: Optional[str] = Field(
        None,
        description="Optional chunk identifier from memory metadata",
    )
    hash: Optional[str] = Field(
        None,
        description="Optional content hash from memory metadata",
    )
    doc_id: Optional[str] = Field(
        None,
        description="Document key or ID for full retrieval",
    )
    doc_key: Optional[str] = Field(
        None,
        description="Original document key (e.g. file::path)",
    )


class ChatMetadata(JarvisModel):
    """Metadata for a chat answer, including cost and status."""

    status: str = Field(
        "ok",
        description="Status of the answer: ok | insufficient_context | error",
    )
    llm_provider: Optional[str] = Field(
        None,
        description="LLM provider that generated the answer",
    )
    model: Optional[str] = Field(
        None,
        description="LLM model identifier",
    )
    total_tokens: int = Field(
        0,
        ge=0,
        description="Total tokens used (input + output)",
    )
    cost_usd: float = Field(
        0.0,
        ge=0.0,
        description="Approximate cost in USD for this answer",
    )
    grounding_level: Optional[str] = Field(
        None,
        description="Grounding level used for this answer (soft | balanced | strict)",
    )
    gap_analysis: Optional["ChatGapAnalysis"] = Field(
        None,
        description="Coverage/recency/coherence gap summary for this query.",
    )
    research_enabled: bool = Field(
        False,
        description="Whether the user requested research mode for this query.",
    )
    research_summary: Optional["ChatResearchSummary"] = Field(
        None,
        description="Optional research plan/execution summary when research is enabled.",
    )
    # Memory Attribution (Story 4.5.2)
    agent_attributions: Optional[dict[str, "AgentAttribution"]] = Field(
        None,
        description="Per-agent memory attribution when Council of Ricks is used.",
    )


class AgentAttribution(JarvisModel):
    """Memory attribution for a single agent's response (Story 4.5.2).
    
    Tracks which memory chunks, domains, and sources each agent used
    to generate its response, enabling traceability of reasoning.
    """

    chunks_used: List[str] = Field(
        default_factory=list,
        description="Chunk IDs actually cited in the agent's response",
    )
    domains_accessed: List[str] = Field(
        default_factory=list,
        description="Domains the cited chunks come from",
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Source document keys",
    )
    memory_freshness: float = Field(
        0.0,
        description="Average freshness score of cited chunks (0.0-1.0)",
    )
    total_chunks_available: int = Field(
        0,
        description="Total chunks available in context",
    )
    citation_rate: float = Field(
        0.0,
        description="Ratio of chunks cited vs available",
    )


class ChatGapAnalysis(JarvisModel):
    """Gap detection scores for coverage, recency, and coherence."""

    coverage_score: float = Field(..., ge=0.0, le=1.0)
    coverage_gap: bool = Field(..., description="True if coverage is below threshold.")
    grounded_terms: list[str] = Field(default_factory=list)
    missing_terms: list[str] = Field(default_factory=list)
    recency_status: str = Field(..., description="MISSING | SPARSE | STALE | FRESH")
    recency_gap: bool = Field(..., description="True if recency is SPARSE/STALE/MISSING.")
    recency_average_days: Optional[float] = Field(
        None,
        description="Average age (days) across retrieved sources.",
    )
    recency_newest_days: Optional[float] = Field(None, description="Newest source age in days.")
    recency_oldest_days: Optional[float] = Field(None, description="Oldest source age in days.")
    coherence_score: float = Field(..., ge=0.0, le=1.0)
    contradictory: bool = Field(..., description="True if coherence is below threshold.")
    pair_count: int = Field(..., ge=0, description="Pairwise comparisons evaluated.")


class ChatResearchSummary(JarvisModel):
    """High-level summary of research planning/execution."""

    triggered: bool = Field(..., description="True when gap thresholds triggered research.")
    reason: Optional[str] = Field(None, description="Short reason for triggering research.")
    planned_queries: list[str] = Field(default_factory=list, description="Queries the planner generated.")
    executed_queries: int = Field(0, ge=0, description="Queries executed via MCP tools.")
    sources_collected: int = Field(0, ge=0, description="Total sources fetched across executed queries.")
    confidence_before: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_after: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_delta: Optional[float] = Field(None, description="After - before confidence.")


class PrimaryDoc(JarvisModel):
    """Primary document reference for full document viewer (Story 4-9).
    
    When present, the UI can fetch and display the full document
    below the LLM answer.
    """

    doc_key: Optional[str] = Field(
        None,
        description="Logical document key for fetching full content",
    )
    source_file: Optional[str] = Field(
        None,
        description="Source file path (for display)",
    )
    domain: Optional[str] = Field(
        None,
        description="Domain label",
    )


class ChatResponse(JarvisModel):
    """Response model for chat-style answers."""

    conversation_id: UUID = Field(..., description="Conversation ID associated with this exchange")
    message_id: UUID = Field(..., description="Assistant message ID for this answer")
    query: str = Field(..., description="Original user question/message")
    response: Optional[str] = Field(
        None,
        description="LLM-generated answer text (None if insufficient context)",
    )
    sources: List[ChatSource] = Field(
        default_factory=list,
        description="Context snippets used to ground the answer",
    )
    metadata: ChatMetadata = Field(
        ...,
        description="LLM and retrieval metadata for this answer",
    )
    trace_id: Optional[str] = Field(
        None,
        description="Story 4.5.6: Cognitive trace ID for debugging this request",
    )
    primary_doc: Optional[PrimaryDoc] = Field(
        None,
        description="Story 4-9: Primary document for 'View full document' feature in META mode",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "message_id": "789e0123-e89b-12d3-a456-426614174999",
                "query": "How does the Jarvis knowledge pipeline work?",
                "response": "Jarvis uses a multi-stage ingestion and retrieval pipeline...",
                "sources": [
                    {
                        "id": 1,
                        "content": "The knowledge pipeline ingests documents from...",
                        "source_file": "docs/jarvis-knowledge-pipeline.md",
                        "section": "Overview",
                        "domain": "jarvis-core",
                        "relevance_score": 0.92,
                        "score": 0.92,
                        "chunk_id": "chunk-001",
                        "hash": "abc123",
                    }
                ],
                "metadata": {
                    "status": "ok",
                    "llm_provider": "openrouter",
                    "model": "google/gemini-2.0-flash-exp:free",
                    "total_tokens": 512,
                    "cost_usd": 0.0,
                    "grounding_level": "balanced",
                    "research_enabled": False,
                    "gap_analysis": {
                        "coverage_score": 0.65,
                        "coverage_gap": False,
                        "grounded_terms": ["knowledge", "pipeline"],
                        "missing_terms": ["latency"],
                        "recency_status": "FRESH",
                        "recency_gap": False,
                        "recency_average_days": 12.5,
                        "recency_newest_days": 2.0,
                        "recency_oldest_days": 28.0,
                        "coherence_score": 0.72,
                        "contradictory": False,
                        "pair_count": 3,
                    },
                    "research_summary": {
                        "triggered": False,
                        "reason": "coverage_ok",
                        "planned_queries": [],
                        "executed_queries": 0,
                        "sources_collected": 0,
                        "confidence_before": 0.5,
                        "confidence_after": 0.5,
                        "confidence_delta": 0.0,
                    },
                },
            }
        }
    )


# Resolve forward references for gap analysis in metadata
ChatMetadata.model_rebuild()
