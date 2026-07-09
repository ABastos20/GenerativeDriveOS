"""Chat processing phase helpers.

Extracted from ChatController.process_chat to reduce LOC and complexity.
"""
from typing import List, Optional, Tuple
from pathlib import Path
import re
import os

from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.jarvis.api.schemas import ChatRequest, ChatMetadata
from src.jarvis.database.models import Message
from jarvis.memory import search as memory_search
from jarvis.llm.client import call_llm
from src.jarvis.utils import chat_utils


def resolve_parameters(request: ChatRequest, settings) -> Tuple[str, str, float, int]:
    """Phase 1: Resolve effective parameters from request and settings."""
    default_retriever = getattr(getattr(settings, "query", None), "default_retriever", "semantic")
    default_weight = getattr(getattr(settings, "query", None), "default_weight", 0.7)
    default_strict_mode = getattr(getattr(settings, "query", None), "default_strict_mode", False)
    default_enable_expansion = getattr(getattr(settings, "query", None), "enable_expansion", False)
    default_expansion_count = getattr(getattr(settings, "query", None), "expansion_count", 2)
    default_grounding_level = getattr(getattr(settings, "query", None), "default_grounding_level", "balanced")

    question = request.message
    
    # Grounding level
    if request.auto_grounding and request.grounding_level is None:
        from jarvis.memory.intent_analyzer import analyze_intent
        intent = analyze_intent(question)
        effective_grounding_level = intent.grounding_level
    else:
        effective_grounding_level = (request.grounding_level or default_grounding_level or "balanced").lower()

    if effective_grounding_level not in {"soft", "balanced", "strict"}:
        raise HTTPException(status_code=400, detail="Invalid grounding_level")

    # Retriever and weight
    effective_retriever = (request.retriever or default_retriever or "semantic").lower()
    effective_weight = request.weight if request.weight is not None else default_weight

    # Strict mode override
    if request.strict_mode or bool(default_strict_mode):
        effective_grounding_level = "strict"

    # Expansion
    if request.expand is not None:
        effective_expansion = request.expand
    elif default_enable_expansion:
        effective_expansion = default_expansion_count
    else:
        effective_expansion = 0

    return effective_grounding_level, effective_retriever, effective_weight, effective_expansion


def validate_parameters(k: int, expansion: int, retriever: str, weight: float):
    """Phase 2: Validate parameters."""
    if not (1 <= k <= 20):
        raise HTTPException(status_code=400, detail="k must be between 1 and 20")
    if expansion < 0 or expansion > 5:
        raise HTTPException(status_code=400, detail="expand must be between 0 and 5")
    if retriever not in {"semantic", "keyword", "hybrid"}:
        raise HTTPException(status_code=400, detail="Invalid retriever")
    if retriever == "hybrid" and not (0.0 <= weight <= 1.0):
        raise HTTPException(status_code=400, detail="weight must be between 0.0 and 1.0")


def setup_conversation_context(db: Session, request: ChatRequest) -> Tuple[any, str]:
    """Phase 3: Setup conversation and build history context."""
    conversation = chat_utils.ensure_conversation(db, request.conversation_id, request.user_id)
    
    history_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    recent_history = history_messages[-8:]
    conversation_lines = []
    hint_pattern = re.compile(r"\s*---\s*\*You can view the full document below in the \"View full .*\" panel\.\*")

    for msg in recent_history:
        content = msg.content.strip()
        if msg.role == "assistant":
            content = hint_pattern.sub("", content).strip()
        role_label = "User" if msg.role == "user" else "Jarvis" if msg.role == "assistant" else msg.role.title()
        conversation_lines.append(f"{role_label}: {content}")
    
    conversation_block = "\n".join(conversation_lines)
    return conversation, conversation_block


def perform_retrieval(
    question: str,
    k: int,
    retriever: str,
    weight: float,
    expansion: int,
    domains: Optional[List[str]],
    arches_session: any,
) -> List:
    """Phase 4: Perform memory retrieval."""
    retrieval_mode = getattr(arches_session, 'retrieval_mode', None)
    time_slice_str = None
    if hasattr(arches_session, 'time_slice_date') and arches_session.time_slice_date:
        time_slice_str = arches_session.time_slice_date.strftime("%Y-%m-%d")
    
    try:
        if expansion > 0:
            results = memory_search.expanded_search(
                question, k=k, expansion_count=expansion,
                domains=domains, retriever=retriever, weight=weight
            )
        else:
            if retriever == "semantic":
                results = memory_search.search_memory(
                    question, k=k, domains=domains,
                    retrieval_mode=retrieval_mode, time_slice=time_slice_str
                )
            elif retriever == "keyword":
                results = memory_search.keyword_search(question, k=k, domains=domains)
            else:
                results = memory_search.hybrid_search(
                    question, k=k, weight=weight, domains=domains
                )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Memory search failed: {exc}") from exc

    results = memory_search.deduplicate_results(results)
    results = chat_utils.order_results_for_mode(results, retrieval_mode)
    return results


def resolve_primary_document(
    db: Session,
    conversation_id: int,
    question: str,
    results: List,
    retrieval_mode: Optional[str],
) -> Optional[dict]:
    """Phase 5: Resolve primary document."""
    SCORE_THRESHOLD = 0.01
    EXPLICIT_INTENT_PATTERN = re.compile(
        r"(retrieve|show|get|give|view|open|see).*(file|doc|document|source|link)|(main|full)\s+documentation|in\s+what\s+file",
        re.IGNORECASE
    )
    has_explicit_intent = bool(EXPLICIT_INTENT_PATTERN.search(question))

    primary_doc_dict = chat_utils.select_primary_doc(db, retrieval_mode, results, score_threshold=SCORE_THRESHOLD)

    if has_explicit_intent:
        stored_doc = chat_utils.get_stored_primary_doc(db, conversation_id)
        if stored_doc:
            new_score = primary_doc_dict.get("score", 0.0) if primary_doc_dict else 0.0
            if primary_doc_dict and primary_doc_dict["doc_key"] != stored_doc["doc_key"]:
                new_filename = Path(primary_doc_dict.get("source_file", "")).name
                is_named_file = new_filename and (new_filename.lower() in question.lower())
                if not is_named_file and new_score < 0.60:
                    primary_doc_dict = stored_doc
            elif not primary_doc_dict:
                primary_doc_dict = stored_doc

    if primary_doc_dict:
        chat_utils.persist_primary_doc(db, conversation_id, primary_doc_dict)
    else:
        stored_doc = chat_utils.get_stored_primary_doc(db, conversation_id)
        if stored_doc:
            primary_doc_dict = stored_doc

    return primary_doc_dict


def build_llm_prompts(
    question: str,
    results: List,
    conversation_block: str,
    grounding_level: str,
    persona: Optional[str] = None,
) -> Tuple[str, str]:
    """Phase 6: Build system and user prompts."""
    # System prompt
    base = """You are JARVIS, an AI advisor with access to a curated knowledge base.
There are TWO layers of context:
1) Immediate chat history (PRIMARY for intent/tone).
2) Long-term knowledge base (SUPPORTING for facts).
Rules:
- Trust conversation for "what we are doing now".
- Trust knowledge base for facts/details.
- Cite sources using [1], [2] etc.
"""
    if grounding_level == "soft":
        base += "\nGROUNDING: SOFT. Be creative, tie claims to sources where possible."
    elif grounding_level == "balanced":
        base += "\nGROUNDING: BALANCED. Cite sources for claims. Label speculation."
    elif grounding_level == "strict":
        base += "\nGROUNDING: STRICT. Do NOT invent facts. If context insufficient, say so."

    # Persona Injection (Story 11-1-b)
    if persona:
        p = persona.lower()
        if "iron" in p:
            base += "\nSTYLE: Decisive, high-agency, direct. You are confident and concise."
        elif "copilot" in p:
            base += "\nSTYLE: Supportive, collaborative. You are a helpful Pair Programmer."
        elif "advisor" in p:
            base += "\nSTYLE: Analytical, long-horizon, cautious. You are a Strategic Advisor."
    
    system_prompt = base

    # User prompt
    context_parts = []
    for idx, res in enumerate(results, start=1):
        source_file = res.source_file or "unknown"
        source_name = Path(source_file).name
        domain = res.domain or "?"
        context_parts.append(f"[Source {idx} | {source_name} | domain:{domain}]\n{res.text.strip()}")
    context_block = "\n\n".join(context_parts)

    user_prompt = f"""Conversation history (most recent last):
{conversation_block}

---

Retrieved Context (Knowledge Base):
{context_block}

---

User's next message: {question}

Answer the message using the retrieved context and conversation history."""

    return system_prompt, user_prompt


def build_chat_response(
    db: Session,
    conversation,
    request: ChatRequest,
    llm_response,
    results: List,
    gap_analysis,
    grounding_level: str,
    research_summary,
) -> "ChatResponse":
    """Phase 9: Build final response and save messages."""
    from src.jarvis.api.schemas import ChatResponse, ChatMetadata

    total_tokens = llm_response.input_tokens + llm_response.output_tokens
    metadata = ChatMetadata(
        status="ok",
        llm_provider=llm_response.provider,
        model=llm_response.model,
        total_tokens=total_tokens,
        cost_usd=float(llm_response.cost_usd),
        grounding_level=grounding_level,
        gap_analysis=gap_analysis,
        research_enabled=request.enable_research,
        research_summary=research_summary,
    )

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=llm_response.content,
        cost_usd=metadata.cost_usd,
        provider=metadata.llm_provider,
        model=metadata.model,
        token_count=total_tokens,
        citation_provenance=[],
    )
    db.add(assistant_message)
    db.flush()

    sources = [
        {
            "id": idx,
            "content": r.text,
            "doc_id": r.doc_id,
            "doc_key": r.doc_key,
            "source_file": r.source_file,
            "section": r.section,
            "domain": r.domain,
            "relevance_score": r.score,
            "score": r.score,
            "chunk_id": getattr(r, "chunk_id", None),
            "hash": getattr(r, "hash", None),
        }
        for idx, r in enumerate(results, start=1)
    ]

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        query=request.message,
        response=llm_response.content,
        sources=sources,
        metadata=metadata,
    )
