from __future__ import annotations

import re
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import structlog

from jarvis.database import models as db_models
from jarvis.memory import search as memory_search
from jarvis.memory.search import RetrievalMode
from jarvis.memory.gap_analyzer import (
    CoherenceAnalyzer,
    CoverageAnalyzer,
    GapAnalysisConfig,
    RecencyAnalyzer,
)
from jarvis.memory.research_planner import ResearchPlanConfig
from jarvis.memory.research_limits import ResearchLimitConfig
from src.jarvis.api.schemas import ChatGapAnalysis
from src.jarvis.database.models import Conversation, Message, ConversationPrimaryDoc

logger = structlog.get_logger(__name__)

def order_results_for_mode(
    results: List[memory_search.SearchResult],
    retrieval_mode,
) -> List[memory_search.SearchResult]:
    """Reorder results to prioritize core sources in META mode."""
    if retrieval_mode != RetrievalMode.META:
        return results
    
    core = []
    non_core = []
    for r in results:
        domain = (r.domain or "").lower()
        semantic_family = ((r.metadata or {}).get("semantic_family") or "").lower()
        
        if domain in ("jarvis-core", "jarvis.core") or semantic_family == "core-memory":
            core.append(r)
        else:
            non_core.append(r)
    
    return core + non_core

def select_primary_doc(db: Session, retrieval_mode: str, results: list, score_threshold: float = 0.45) -> Optional[dict]:
    """Select the most relevant document to be the 'primary' document for the UI."""
    def _get_doc_key(r):
        if r.doc_key:
            return r.doc_key
        if r.source_file:
            return f"file::{r.source_file}"
        return None
    
    if not results:
        return None
    
    if retrieval_mode == RetrievalMode.META:
        for r in results:
            if r.source_file and r.source_file.endswith("memory.core.md"):
                return {
                    "doc_key": _get_doc_key(r),
                    "source_file": r.source_file,
                    "domain": r.domain,
                    "score": r.score,
                }
    
    r = results[0]
    doc_key = _get_doc_key(r)
    
    if retrieval_mode != RetrievalMode.META and r.score < score_threshold:
        return None

    if doc_key or r.source_file:
        return {
            "doc_key": doc_key,
            "source_file": r.source_file,
            "domain": r.domain,
            "score": r.score,
        }
    
    return None

def persist_primary_doc(db: Session, conversation_id: UUID, primary_doc: dict) -> None:
    """Upsert primary doc for conversation."""
    existing = db.query(ConversationPrimaryDoc).filter(
        ConversationPrimaryDoc.conversation_id == conversation_id
    ).first()
    
    if existing:
        existing.doc_key = primary_doc["doc_key"]
        existing.source_file = primary_doc.get("source_file")
        existing.domain = primary_doc.get("domain")
    else:
        db.add(ConversationPrimaryDoc(
            conversation_id=conversation_id,
            doc_key=primary_doc["doc_key"],
            source_file=primary_doc.get("source_file"),
            domain=primary_doc.get("domain"),
        ))
    db.flush()
    logger.info(
        "primary_doc_persisted",
        conversation_id=str(conversation_id),
        doc_key=primary_doc["doc_key"],
    )

def get_stored_primary_doc(db: Session, conversation_id: UUID) -> Optional[dict]:
    """Get stored primary doc for conversation if exists."""
    stored = db.query(ConversationPrimaryDoc).filter(
        ConversationPrimaryDoc.conversation_id == conversation_id
    ).first()
    if stored:
        return {
            "doc_key": stored.doc_key,
            "source_file": stored.source_file,
            "domain": stored.domain,
        }
    return None

def sanitize_null_bytes(data):
    """Recursively remove null bytes from strings."""
    if isinstance(data, str):
        return data.replace('\x00', '')
    elif isinstance(data, dict):
        return {k: sanitize_null_bytes(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_null_bytes(item) for item in data]
    else:
        return data

def load_gap_config(settings: object) -> GapAnalysisConfig:
    gap_cfg = getattr(settings, "gap_analysis", None)
    return GapAnalysisConfig(
        coverage_threshold=getattr(gap_cfg, "coverage_threshold", 0.6),
        recency_stale_days=getattr(gap_cfg, "recency_stale_days", 90),
        recency_sparse_days=getattr(gap_cfg, "recency_sparse_days", 30),
        min_recency_results=getattr(gap_cfg, "min_recency_results", 1),
        coherence_threshold=getattr(gap_cfg, "coherence_threshold", 0.35),
    )

def load_research_config(settings: object) -> ResearchPlanConfig:
    research_cfg = getattr(settings, "research", None)
    return ResearchPlanConfig(
        max_queries=getattr(research_cfg, "max_queries", 3),
        min_queries=getattr(research_cfg, "min_queries", 2),
        provider=getattr(research_cfg, "provider", "auto"),
    )

def load_research_limit_config(settings: object) -> ResearchLimitConfig:
    research_cfg = getattr(settings, "research", None)
    return ResearchLimitConfig(
        hourly_limit=getattr(research_cfg, "hourly_limit", 10),
        cost_cap_usd=float(getattr(research_cfg, "cost_cap_usd", 2.0)),
        redis_url=getattr(research_cfg, "redis_url", None),
    )

def analyze_gaps(
    question: str,
    results: list[memory_search.SearchResult],
    coverage_analyzer: CoverageAnalyzer,
    recency_analyzer: RecencyAnalyzer,
    coherence_analyzer: CoherenceAnalyzer,
) -> ChatGapAnalysis:
    coverage = coverage_analyzer.analyze(question, results)
    recency = recency_analyzer.analyze(results)
    coherence = coherence_analyzer.analyze(results)

    return ChatGapAnalysis(
        coverage_score=coverage.coverage_score,
        coverage_gap=coverage.gap_detected,
        grounded_terms=sorted(coverage.grounded_terms),
        missing_terms=sorted(coverage.missing_terms),
        recency_status=recency.status,
        recency_gap=recency.gap_detected,
        recency_average_days=recency.average_age_days,
        recency_newest_days=recency.newest_age_days,
        recency_oldest_days=recency.oldest_age_days,
        coherence_score=coherence.coherence_score,
        contradictory=coherence.contradictory,
        pair_count=coherence.pair_count,
    )

def ensure_conversation(
    db: Session,
    conversation_id: Optional[UUID],
    user_id: str,
) -> Conversation:
    """Get or create a conversation row.
    
    CRITICAL SECURITY: This function enforces ownership. 
    If conversation_id is requested but belongs to another user, raises 403.
    """
    if conversation_id is not None:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found",
            )
        
        # IDOR PROTECTION
        if conversation.user_id != user_id:
            # We explicitly allow "legacy" conversations (user_id=None) to be claimed? 
            # Or should we be strict? Architect said "Lock Dashboards Properly".
            # Let's be strict. If it's not yours, you can't touch it.
            # But what about legacy data? We can migrate it later.
            # For now: 403.
            logger.warning("idor_attempt_blocked", requested_id=str(conversation_id), actual_owner=conversation.user_id, attempter=user_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this conversation.",
            )
            
        return conversation

    conversation = Conversation(user_id=user_id)
    db.add(conversation)
    db.flush()
    return conversation
