"""SQLAlchemy ORM models for JARVIS System database schema.

This module defines the database models for:
- Conversations and messages
- LLM provider registry and usage tracking
- Agent persona configurations

All timestamps are stored in UTC (timezone-aware) per ADR-007.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Conversation(Base):
    """Top-level conversation container.

    Stores metadata about a conversation session between user and JARVIS.
    Related messages are linked via foreign key relationship.
    """

    __tablename__ = "conversations"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility

    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    user_id: Optional[str] = Column(String(255), nullable=True, comment="Future: multi-user support")
    created_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    messages: List["Message"] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, created_at={self.created_at})>"


class Message(Base):
    """Individual message within a conversation.

    Stores user queries and JARVIS responses with full metadata including
    agent persona, cost, LLM provider, and token count.
    """

    __tablename__ = "messages"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility
    __table_args__ = (
        {"comment": "Individual messages within conversations with LLM metadata"},
    )

    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    conversation_id: UUID = Column(
        PGUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: str = Column(String(50), nullable=False, comment="user | assistant | system")
    content: str = Column(Text, nullable=False)
    agent_persona: Optional[str] = Column(
        String(100), nullable=True, comment="Which Rick responded (if applicable)"
    )
    citation_provenance: Optional[dict] = Column(
        JSONB,
        nullable=True,
        comment="Stored citation metadata for assistant messages (sources[], scores, hashes, etc.)",
    )
    voting_metadata: Optional[dict] = Column(
        JSONB,
        nullable=True,
        comment="Council of Ricks voting results and override metadata (Story 4.5)",
    )
    memory_attribution: Optional[dict] = Column(
        JSONB,
        nullable=True,
        comment="Per-agent memory chunk/domain/source attribution (Story 4.5.2)",
    )
    cost_usd: Optional[Decimal] = Column(Numeric(10, 6), nullable=True)
    provider: Optional[str] = Column(String(100), nullable=True)
    model: Optional[str] = Column(String(100), nullable=True)
    token_count: Optional[int] = Column(Integer, nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    # Relationships
    conversation: Conversation = relationship("Conversation", back_populates="messages")
    usage_logs: List["LLMUsageLog"] = relationship(
        "LLMUsageLog", back_populates="message", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, persona={self.agent_persona})>"


class LLMProvider(Base):
    """LLM provider registry for cost-first routing.

    Tracks free-tier and paid LLM providers with quota limits and usage stats.
    Supports the cost-first routing strategy (FR3.1).
    """

    __tablename__ = "llm_providers"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(100), unique=True, nullable=False, comment="openrouter, together_ai, etc.")
    type: str = Column(String(50), nullable=False, comment="free_tier | paid")
    priority: int = Column(Integer, default=100, nullable=False, comment="Lower = higher priority")
    quota_limit: Optional[int] = Column(
        BigInteger, nullable=True, comment="Tokens per month (if known)"
    )
    tokens_used: int = Column(BigInteger, default=0, nullable=False)
    last_reset: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    api_key_env: Optional[str] = Column(String(100), nullable=True, comment="ENV variable name")
    is_active: bool = Column(Boolean, default=True, nullable=False)

    # Relationships
    usage_logs: List["LLMUsageLog"] = relationship("LLMUsageLog", back_populates="provider")

    def __repr__(self) -> str:
        return f"<LLMProvider(id={self.id}, name={self.name}, type={self.type}, active={self.is_active})>"


class LLMUsageLog(Base):
    """Detailed LLM API call tracking for cost analysis.

    Logs every LLM API call with token counts and costs for auditing and
    cost optimization. Supports FR3.3 (Usage Tracking & Cost Calculation).
    """

    __tablename__ = "llm_usage_log"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility
    __table_args__ = (
        {"comment": "Detailed LLM API call tracking for cost analysis"},
    )

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)
    provider_id: int = Column(Integer, ForeignKey("llm_providers.id"), nullable=False, index=True)
    message_id: Optional[UUID] = Column(
        PGUUID(as_uuid=True), ForeignKey("messages.id"), nullable=True, index=True
    )
    model: str = Column(String(100), nullable=False)
    tokens_input: int = Column(Integer, nullable=False)
    tokens_output: int = Column(Integer, nullable=False)
    cost_usd: Decimal = Column(Numeric(10, 6), nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    # Relationships
    provider: LLMProvider = relationship("LLMProvider", back_populates="usage_logs")
    message: Optional[Message] = relationship("Message", back_populates="usage_logs")

    def __repr__(self) -> str:
        return (
            f"<LLMUsageLog(id={self.id}, provider_id={self.provider_id}, "
            f"tokens={self.tokens_input}+{self.tokens_output}, cost=${self.cost_usd})>"
        )


class AgentPersona(Base):
    """Council of Ricks persona configurations.

    Stores agent persona definitions with system prompts and weighted chaos voting weights.
    Supports FR2.1 (Agent Persona Management).
    """

    __tablename__ = "agent_personas"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(
        String(100), unique=True, nullable=False, comment="Rickiest Rick, Supportive Rick, etc."
    )
    system_prompt: str = Column(Text, nullable=False)
    weight: Decimal = Column(
        Numeric(3, 2), nullable=False, comment="0.40, 0.20, 0.10, 0.30 (must sum to 1.00)"
    )
    is_active: bool = Column(Boolean, default=True, nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AgentPersona(id={self.id}, name={self.name}, weight={self.weight}, active={self.is_active})>"


class KnowledgeDomain(Base):
    """Domain taxonomy for multi-domain / multi-persona expertise.

    Stores normalized domain keys (DDD-style bounded contexts, human-science domains,
    product branches, etc.) that can be attached to content and used by the Council
    of Ricks for routing and analytics.
    """

    __tablename__ = "knowledge_domains"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    key: str = Column(
        String(100),
        unique=True,
        nullable=False,
        comment="Stable domain key, e.g. 'architecture.core', 'history.modern'",
    )
    label: str = Column(
        String(200),
        nullable=False,
        comment="Human-readable label for the domain",
    )
    parent_key: Optional[str] = Column(
        String(100),
        nullable=True,
        comment="Optional parent domain key for hierarchical taxonomy",
    )
    kind: str = Column(
        String(50),
        nullable=False,
        default="generic",
        comment="Category of domain: human_science | product_branch | infra | generic",
    )
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<KnowledgeDomain(id={self.id}, key={self.key}, kind={self.kind})>"


class ResearchLog(Base):
    """Research activity log for gap-triggered research sessions."""

    __tablename__ = "research_logs"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility
    __table_args__ = ({"comment": "Research sessions executed via research mode"},)

    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    conversation_id: Optional[UUID] = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    message_id: Optional[UUID] = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    gap_types: Optional[dict] = Column(
        JSONB, nullable=True, comment="Gap types detected (coverage/recency/coherence flags)"
    )
    planned_queries: Optional[dict] = Column(
        JSONB, nullable=True, comment="Queries generated for research mode"
    )
    executed_queries: int = Column(Integer, nullable=False, default=0)
    sources_collected: int = Column(Integer, nullable=False, default=0)
    status: str = Column(String(50), nullable=False, default="pending")
    provider: Optional[str] = Column(String(100), nullable=True)
    model: Optional[str] = Column(String(100), nullable=True)
    cost_usd: Optional[Numeric] = Column(Numeric(10, 6), nullable=True)
    confidence_before: Optional[Numeric] = Column(Numeric(4, 3), nullable=True)
    confidence_after: Optional[Numeric] = Column(Numeric(4, 3), nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<ResearchLog(id={self.id}, status={self.status}, "
            f"queries={self.executed_queries}, sources={self.sources_collected})>"
        )


class TemporalChunk(Base):
    """Versioned knowledge chunk metadata for temporal updates."""

    __tablename__ = "temporal_chunks"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility
    __table_args__ = ({"comment": "Versioned chunk metadata for temporal memory updates"},)

    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    collection: str = Column(String(100), nullable=False, default="knowledge")
    domain: Optional[str] = Column(String(100), nullable=True)
    source_file: Optional[str] = Column(String(500), nullable=True)
    section: Optional[str] = Column(String(200), nullable=True)
    content_hash: str = Column(String(128), nullable=False, index=True)
    source_type: str = Column(String(50), nullable=False, default="web_research")
    verified_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    confidence: Numeric = Column(Numeric(4, 3), nullable=False, default=0.5)
    supersedes: Optional[UUID] = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    extra_metadata: Optional[dict] = Column(JSONB, nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<TemporalChunk(id={self.id}, domain={self.domain}, source_type={self.source_type}, "
            f"supersedes={self.supersedes})>"
        )


class Document(Base):
    """Full text of ingested documents for hybrid retrieval and full-text search.
    
    Stores the complete content of ingested files to enable:
    1. Keyword search (BM25-like via Postgres tsvector)
    2. Full document retrieval by doc_key
    3. Hybrid search combining Qdrant chunks + Postgres full text
    
    Story 4.5.3b: Added version and is_latest for recency filtering at Qdrant level.
    """

    __tablename__ = "documents"
    __allow_unmapped__ = True  # SQLAlchemy 2.0 compatibility

    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    doc_key: str = Column(
        String(500), unique=True, nullable=False, index=True, comment="Stable key e.g. file::/path/to/doc.pdf"
    )
    content: str = Column(Text, nullable=False)
    source_file: str = Column(String(500), nullable=False)
    domain: Optional[str] = Column(String(100), nullable=True)
    metadata_: Optional[dict] = Column(JSONB, nullable=True, name="metadata")
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # Story 4.5.3b: Version tracking for is_latest Qdrant filter
    version: int = Column(
        Integer, nullable=False, default=1, comment="Document version number (incremented on re-ingest)"
    )
    is_latest: bool = Column(
        Boolean, nullable=False, default=True, comment="True if this is the latest version of the doc_key"
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, doc_key={self.doc_key}, domain={self.domain}, v={self.version})>"


class ConversationPrimaryDoc(Base):
    """Persistent primary document reference per conversation (Story 4-13).
    
    Stores the primary document for a conversation, allowing it to persist
    across queries even when subsequent queries don't retrieve it.
    Only used in META mode for core document viewer persistence.
    """

    __tablename__ = "conversation_primary_docs"
    __allow_unmapped__ = True
    __table_args__ = (
        {"comment": "Persistent primary doc per conversation for META mode (Story 4-13)"},
    )

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id: UUID = Column(
        PGUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One primary doc per conversation
        index=True,
    )
    doc_key: str = Column(String(512), nullable=False)
    source_file: Optional[str] = Column(String(512), nullable=True)
    domain: Optional[str] = Column(String(128), nullable=True)
    first_seen_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_used_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ConversationPrimaryDoc(conversation_id={self.conversation_id}, doc_key={self.doc_key})>"


class CognitiveTraceLog(Base):
    """Cognitive trace log for ARCHES query lifecycle (Story 4.5.6).

    Captures full cognitive trace for debugging and replay analysis.
    Trace ownership: ARCHES controller creates, finalizes, persists.
    """


    __tablename__ = "cognitive_traces"
    __allow_unmapped__ = True
    __table_args__ = (
        {"comment": "Cognitive traces for ARCHES query debugging and replay"},
    )

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    trace_id: UUID = Column(
        PGUUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique trace identifier",
    )
    session_id: Optional[str] = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Session ID for grouping traces",
    )
    query: str = Column(Text, nullable=False, comment="User query text")
    mode: str = Column(
        String(50),
        default="qa",
        nullable=False,
        comment="Query mode: qa | research | planning | hybrid",
    )
    severity: str = Column(
        String(50),
        default="normal",
        nullable=False,
        index=True,
        comment="Trace severity: normal | error | low_confidence | debug",
    )
    sampled: bool = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether trace was sampled/retained",
    )
    trace_schema_version: int = Column(
        Integer,
        default=1,
        nullable=False,
        comment="Schema version for trace data compatibility",
    )
    trace_data: dict = Column(
        JSONB,
        nullable=False,
        comment="Full trace data as JSONB",
    )
    total_latency_ms: Optional[int] = Column(
        Integer,
        nullable=True,
        comment="Total query processing time in milliseconds",
    )
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        comment="When trace was recorded",
    )

    def __repr__(self) -> str:
        return f"<CognitiveTraceLog(trace_id={self.trace_id}, mode={self.mode}, severity={self.severity})>"


class Entity(Base):
    """Knowledge Graph Entity."""
    __tablename__ = "entities"
    __allow_unmapped__ = True

    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    name: str = Column(String, index=True, nullable=False)
    kind: Optional[str] = Column(String, index=True, comment="Person, Company, Product, Concept, etc.")
    description: Optional[str] = Column(Text)
    properties: dict = Column(JSONB, default={}, nullable=False)
    
    # Relationships
    created_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Entity(id={self.id}, name={self.name}, kind={self.kind})>"


class Relationship(Base):
    """Knowledge Graph Relationship (Edge)."""
    __tablename__ = "relationships"
    __allow_unmapped__ = True

    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    source_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), index=True, nullable=False)
    target_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), index=True, nullable=False)
    relation_type: str = Column(String, index=True, nullable=False, comment="HAS_PRODUCT, FOUNDED_BY, etc.")
    properties: dict = Column(JSONB, default={}, nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Relationship(source={self.source_id}, target={self.target_id}, type={self.relation_type})>"


class DocumentEntity(Base):
    """Link documents to entities mentioned in them."""
    __tablename__ = "document_entities"
    __allow_unmapped__ = True
    
    document_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    entity_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    confidence: Decimal = Column(Numeric(4, 3), default=1.0, nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<DocumentEntity(doc={self.document_id}, entity={self.entity_id})>"


# =============================================================================
# Phase 9: Epistemic Autonomy Layer Models
# =============================================================================

class EpistemicConflict(Base):
    """Detected contradiction in the knowledge graph.
    
    Tracks when two beliefs about an entity conflict, enabling
    truth maintenance and self-doubt capabilities.
    """
    __tablename__ = "epistemic_conflicts"
    __allow_unmapped__ = True

    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    entity_id: UUID = Column(
        PGUUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"),
        index=True, nullable=False, comment="Primary entity with conflicting beliefs"
    )
    fact_1: str = Column(Text, nullable=False, comment="First belief/claim")
    fact_2: str = Column(Text, nullable=False, comment="Contradicting belief/claim")
    source_1_id: UUID = Column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True, comment="Document source for fact_1"
    )
    source_2_id: UUID = Column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True, comment="Document source for fact_2"
    )
    contradiction_type: str = Column(
        String(50), nullable=False, index=True,
        comment="temporal | source | domain | confidence"
    )
    confidence_delta: Decimal = Column(
        Numeric(4, 3), default=0.0, nullable=False,
        comment="Difference in confidence between beliefs"
    )
    severity: str = Column(
        String(20), default="medium", nullable=False,
        comment="low | medium | high | critical"
    )
    status: str = Column(
        String(20), default="active", nullable=False, index=True,
        comment="active | resolved | deprecated"
    )
    resolution: Optional[str] = Column(
        String(50), nullable=True,
        comment="human_override | auto_reconciled | fact_1_wins | fact_2_wins"
    )
    resolved_by: Optional[str] = Column(String(100), nullable=True)
    detected_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    resolved_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<EpistemicConflict(entity={self.entity_id}, type={self.contradiction_type}, status={self.status})>"


class BeliefSnapshot(Base):
    """Temporal snapshot of a belief about an entity.
    
    Enables tracking how beliefs change over time, supporting
    drift detection and temporal belief queries.
    """
    __tablename__ = "belief_snapshots"
    __allow_unmapped__ = True

    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    entity_id: UUID = Column(
        PGUUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    claim: str = Column(Text, nullable=False, comment="The belief content")
    claim_type: str = Column(
        String(50), nullable=False, index=True,
        comment="property | relationship | classification"
    )
    confidence: Decimal = Column(
        Numeric(4, 3), default=1.0, nullable=False,
        comment="Confidence in this belief (0-1)"
    )
    source_doc_id: UUID = Column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True, comment="Document establishing this belief"
    )
    superseded_by: UUID = Column(
        PGUUID(as_uuid=True), ForeignKey("belief_snapshots.id", ondelete="SET NULL"),
        nullable=True, comment="Link to newer belief that supersedes this"
    )
    is_current: bool = Column(Boolean, default=True, nullable=False, index=True)
    created_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<BeliefSnapshot(entity={self.entity_id}, claim_type={self.claim_type}, current={self.is_current})>"


class Hypothesis(Base):
    """Auto-generated hypothesis for validation.
    
    Generated when the system detects high contradiction regions,
    sparse graph areas, or high uncertainty clusters.
    """
    __tablename__ = "hypotheses"
    __allow_unmapped__ = True

    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    statement: str = Column(Text, nullable=False, comment="The hypothesis text")
    confidence: Decimal = Column(
        Numeric(4, 3), default=0.5, nullable=False,
        comment="Initial confidence (0-1)"
    )
    trigger_type: str = Column(
        String(50), nullable=False, index=True,
        comment="contradiction | sparse_region | uncertainty"
    )
    supporting_entities: dict = Column(
        JSONB, default=list, nullable=False,
        comment="List of entity UUIDs supporting this hypothesis"
    )
    contradicting_entities: dict = Column(
        JSONB, default=list, nullable=False,
        comment="List of entity UUIDs contradicting this hypothesis"
    )
    validation_plan: dict = Column(
        JSONB, default=list, nullable=False,
        comment="List of validation steps: [search:X, papers:Y, ask_user]"
    )
    status: str = Column(
        String(20), default="pending", nullable=False, index=True,
        comment="pending | validating | validated | rejected | escalated"
    )
    validated_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Hypothesis(statement={self.statement[:50]}..., status={self.status})>"


class ModelPerformance(Base):
    """Performance tracking for LLM models per domain.
    
    Enables dynamic model selection and trust calibration.
    """
    __tablename__ = "model_performance"
    __allow_unmapped__ = True

    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    model_name: str = Column(String(100), nullable=False, index=True)
    domain: str = Column(String(100), nullable=False, index=True)
    total_calls: int = Column(Integer, default=0, nullable=False)
    avg_latency_ms: Decimal = Column(Numeric(10, 2), default=0.0, nullable=False)
    hallucination_count: int = Column(Integer, default=0, nullable=False)
    conflict_generation_rate: Decimal = Column(
        Numeric(4, 3), default=0.0, nullable=False,
        comment="Rate of conflicts generated by this model"
    )
    token_efficiency: Decimal = Column(
        Numeric(4, 3), default=1.0, nullable=False,
        comment="useful_tokens / total_tokens"
    )
    last_used: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    updated_at: datetime = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ModelPerformance(model={self.model_name}, domain={self.domain}, calls={self.total_calls})>"


# =============================================================================
# Story 11-5: Knowledge Sovereignty & Provenance Arbitration (Lock 7)
# =============================================================================

class KnowledgeUnit(Base):
    """Knowledge unit with immutable tier and provenance.

    Every piece of knowledge stored in JARVIS has an immutable tier
    that determines its epistemic status and usage constraints.

    Story 11-5 implements Lock 7 (Epistemic Sovereignty):
    "The system cannot lie to itself"

    Tier Lattice: K0 ≺ K1 ≺ K2 ≺ K3 ≺ K4
    - K0: Ground Truth (telemetry, sensors)
    - K1: Verified Derivation (internal analytics)
    - K2: Trust-Scored External (peer-review, standards)
    - K3: Narrative (news, blogs, commentary)
    - K4: Noise (social media, forums, scrapes)
    """
    __tablename__ = "knowledge_units"
    __allow_unmapped__ = True

    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )

    # Content
    content: str = Column(Text, nullable=False, comment="The knowledge content/claim")
    content_hash: str = Column(
        String(64), nullable=False, index=True,
        comment="SHA-256 hash of content for deduplication"
    )

    # Tier & Provenance (Immutable)
    knowledge_tier: str = Column(
        String(50), nullable=False, index=True,
        comment="K0 | K1 | K2 | K3 | K4 - IMMUTABLE except via constitutional transition"
    )
    source_type: str = Column(
        String(100), nullable=False,
        comment="telemetry | paper | news | scrape | etc."
    )
    origin: str = Column(
        String(500), nullable=False,
        comment="DOI, URL, file path, sensor ID, etc."
    )
    collection_method: str = Column(
        String(100), nullable=False,
        comment="direct_capture | api_fetch | web_fetch | etc."
    )

    # Trust Dynamics
    initial_confidence: Numeric = Column(
        Numeric(4, 3), nullable=False, default=1.0,
        comment="Initial confidence c₀ ∈ [0,1]"
    )
    current_trust: Numeric = Column(
        Numeric(4, 3), nullable=False, default=1.0,
        comment="Current trust T(i,t) with decay applied"
    )
    last_trust_update: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Last time trust was recalculated"
    )

    # Provenance Lineage
    provenance_hash: str = Column(
        String(64), nullable=False, index=True,
        comment="SHA-256 hash of provenance vector for integrity"
    )
    parent_id: Optional[UUID] = Column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_units.id", ondelete="SET NULL"),
        nullable=True,
        comment="Parent knowledge unit if derived"
    )

    # Timestamps
    ingestion_time: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        comment="When this knowledge was first ingested (t₀)"
    )
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Metadata
    metadata_: Optional[dict] = Column(
        JSONB, nullable=True, name="metadata",
        comment="Additional provenance metadata"
    )

    # Status
    is_frozen: bool = Column(
        Boolean, default=False, nullable=False,
        comment="True if frozen due to dual-persona arbitration disagreement"
    )
    is_archived: bool = Column(
        Boolean, default=False, nullable=False, index=True,
        comment="True if trust decayed below threshold"
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeUnit(id={self.id}, tier={self.knowledge_tier}, "
            f"trust={self.current_trust}, frozen={self.is_frozen})>"
        )


class ProvenanceLedgerEntry(Base):
    """Append-only provenance ledger for knowledge units.

    Cryptographically sealed audit trail of all knowledge provenance.
    Implements AC #2: Provenance Ledger.

    Provenance Vector: P(i) = ⟨s, o, m, c₀, t₀, K⟩
    Where:
    - s = source_type
    - o = origin
    - m = collection_method
    - c₀ = initial_confidence
    - t₀ = ingestion_time
    - K = knowledge_tier
    """
    __tablename__ = "provenance_ledger"
    __allow_unmapped__ = True
    __table_args__ = (
        {"comment": "Append-only cryptographically sealed provenance audit trail"},
    )

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)

    # Link to knowledge unit
    knowledge_unit_id: UUID = Column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Provenance Vector Components
    source_type: str = Column(String(100), nullable=False)
    origin: str = Column(String(500), nullable=False)
    collection_method: str = Column(String(100), nullable=False)
    initial_confidence: Numeric = Column(Numeric(4, 3), nullable=False)
    ingestion_time: datetime = Column(DateTime(timezone=True), nullable=False)
    knowledge_tier: str = Column(String(50), nullable=False)

    # Cryptographic Seal
    provenance_hash: str = Column(
        String(64), nullable=False, unique=True, index=True,
        comment="SHA-256(source_type||origin||method||c₀||t₀||K)"
    )
    previous_hash: Optional[str] = Column(
        String(64), nullable=True,
        comment="Hash of previous entry for blockchain-style chain"
    )

    # Lineage
    parent_ledger_id: Optional[int] = Column(
        BigInteger,
        ForeignKey("provenance_ledger.id", ondelete="SET NULL"),
        nullable=True,
        comment="Parent entry if knowledge was derived"
    )

    # Metadata
    metadata_: Optional[dict] = Column(
        JSONB, nullable=True, name="metadata",
        comment="Additional context"
    )

    # Timestamp (immutable)
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return (
            f"<ProvenanceLedgerEntry(id={self.id}, ku_id={self.knowledge_unit_id}, "
            f"tier={self.knowledge_tier}, hash={self.provenance_hash[:8]}...)>"
        )


class TrustScore(Base):
    """Trust score history for knowledge units.

    Tracks trust evolution over time with decay dynamics.
    Implements AC #4: Trust Weight & Decay Engine.

    Trust Formula: T(i,t) = c₀(i) · e^(-λ_K · (t - t₀))
    """
    __tablename__ = "trust_scores"
    __allow_unmapped__ = True

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)

    knowledge_unit_id: UUID = Column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Trust Value
    trust_value: Numeric = Column(
        Numeric(4, 3), nullable=False,
        comment="Trust score T(i,t) ∈ [0,1]"
    )

    # Decay Parameters
    decay_rate: Numeric = Column(
        Numeric(10, 8), nullable=False,
        comment="λ_K decay rate (tier-dependent)"
    )

    # Events
    event_type: str = Column(
        String(50), nullable=False, index=True,
        comment="initial | decay | refresh | contradiction_penalty | expiry"
    )
    event_reason: Optional[str] = Column(Text, nullable=True)

    # Timestamp
    calculated_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return (
            f"<TrustScore(ku_id={self.knowledge_unit_id}, trust={self.trust_value}, "
            f"event={self.event_type})>"
        )


class TierTransitionLog(Base):
    """Audit log for all tier transitions (promotions/demotions).

    Implements tier immutability enforcement from AC #1.
    All tier changes require audit trail and authorization.
    """
    __tablename__ = "tier_transition_log"
    __allow_unmapped__ = True
    __table_args__ = (
        {"comment": "Audit trail for knowledge tier promotions and demotions"},
    )

    id: int = Column(BigInteger, primary_key=True, autoincrement=True)

    knowledge_unit_id: UUID = Column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Transition Details
    from_tier: str = Column(String(50), nullable=False)
    to_tier: str = Column(String(50), nullable=False)
    transition_type: str = Column(
        String(20), nullable=False, index=True,
        comment="promotion | demotion"
    )

    # Authorization
    reason: str = Column(Text, nullable=False)
    authorized_by: Optional[str] = Column(
        String(255), nullable=True,
        comment="Governance user or system component"
    )
    authorization_required: bool = Column(Boolean, nullable=False)

    # Dual-Persona Arbitration (AC #3)
    analyst_verdict: Optional[bool] = Column(
        Boolean, nullable=True,
        comment="Analyst persona approval (True/False/None if N/A)"
    )
    adversary_verdict: Optional[bool] = Column(
        Boolean, nullable=True,
        comment="Adversary persona approval (True/False/None if N/A)"
    )

    # Timestamp
    transitioned_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return (
            f"<TierTransitionLog(ku_id={self.knowledge_unit_id}, "
            f"{self.from_tier} → {self.to_tier}, type={self.transition_type})>"
        )


class EpistemicEventModel(Base):
    """Database model for epistemic audit events (Story 11-5.4).
    
    Persists audit events for long-term storage and SQL querying.
    Uses JSONB for flexible payload storage.
    
    Story 11-5.4: PostgreSQL Persistence Sink
    """
    __tablename__ = "epistemic_events"
    __allow_unmapped__ = True
    __table_args__ = (
        {"comment": "Epistemic audit events for compliance and forensic reconstruction"},
    )
    
    id: UUID = Column(
        PGUUID(as_uuid=True), primary_key=True,
        comment="Event UUID"
    )
    event_type: str = Column(
        String(50), nullable=False, index=True,
        comment="promotion | demotion | decay | freeze | contradiction | usage_violation"
    )
    knowledge_unit_id: UUID = Column(
        PGUUID(as_uuid=True), nullable=False, index=True,
        comment="ID of affected knowledge unit"
    )
    timestamp: datetime = Column(
        DateTime(timezone=True), nullable=False, index=True,
        comment="Event timestamp (UTC)"
    )
    payload: dict = Column(
        JSONB, nullable=False,
        comment="Full event data as JSON"
    )
    
    def __repr__(self) -> str:
        return f"<EpistemicEventModel(id={self.id}, type={self.event_type}, timestamp={self.timestamp})>"
