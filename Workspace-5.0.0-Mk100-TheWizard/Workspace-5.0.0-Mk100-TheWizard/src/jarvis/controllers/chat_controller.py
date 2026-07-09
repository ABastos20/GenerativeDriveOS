from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import structlog

from jarvis.config import load_settings
from jarvis.database import models as db_models
from jarvis.llm.client import call_llm
from jarvis.memory import search as memory_search
from jarvis.memory.gap_analyzer import (
    CoherenceAnalyzer,
    CoverageAnalyzer,
    RecencyAnalyzer,
)
from jarvis.memory.research_executor import MCPResearchExecutor
from jarvis.memory.research_planner import ResearchPlanner
from jarvis.memory.critical_integrator import CriticalIntegrator
from jarvis.memory.research_limits import ResearchLimiter
from jarvis.memory.intent_analyzer import analyze_intent
from jarvis.arches.controller import get_controller, PlanStage
from src.jarvis.api.schemas import (
    ChatMetadata,
    ChatRequest,
    ChatResponse,
    ChatResearchSummary,
)
from src.jarvis.database.models import Message
from src.jarvis.utils import chat_utils

logger = structlog.get_logger(__name__)

class ChatController:
    def __init__(self, db: Session):
        self.db = db
        self.settings = load_settings()
        self.gap_config = chat_utils.load_gap_config(self.settings)
        self.research_config = chat_utils.load_research_config(self.settings)
        self.research_limit_config = chat_utils.load_research_limit_config(self.settings)
        
        self.coverage_analyzer = CoverageAnalyzer(self.gap_config)
        self.recency_analyzer = RecencyAnalyzer(self.gap_config)
        self.coherence_analyzer = CoherenceAnalyzer(self.gap_config)
        self.planner = ResearchPlanner(self.research_config)
        self.executor = MCPResearchExecutor(self.research_config)
        self.integrator = CriticalIntegrator()

    def process_chat(self, request: ChatRequest) -> ChatResponse:
        from src.jarvis.controllers.chat_phases import (
            resolve_parameters,
            validate_parameters,
            setup_conversation_context,
            perform_retrieval,
            resolve_primary_document,
            build_llm_prompts,
        )

        try:
            # Phase 1: Parameter Resolution
            effective_grounding_level, effective_retriever, effective_weight, effective_expansion = resolve_parameters(
                request, self.settings
            )
            is_strict = effective_grounding_level == "strict"

            # Phase 2: Validation
            validate_parameters(request.k, effective_expansion, effective_retriever, effective_weight)

            # Phase 3: Conversation Context
            conversation, conversation_block = setup_conversation_context(self.db, request)

            domains = [request.source] if request.source else None

            # ARCHES Integration
            arches_controller = get_controller()
            arches_session = arches_controller.start_session(
                query=request.message,
                conversation_id=str(conversation.id) if conversation else None,
            )
            arches_controller.start_stage(arches_session, PlanStage.HYBRID)

            # Phase 4: Retrieval
            results = perform_retrieval(
                request.message, request.k, effective_retriever, effective_weight,
                effective_expansion, domains, arches_session
            )

            # Phase 5: Primary Doc
            retrieval_mode = getattr(arches_session, 'retrieval_mode', None)
            primary_doc_dict = resolve_primary_document(
                self.db, conversation.id, request.message, results, retrieval_mode
            )

            arches_controller.complete_stage(arches_session, PlanStage.HYBRID)
            arches_controller.record_memory_usage(arches_session, results, domains=domains)
            arches_controller.start_stage(arches_session, PlanStage.ASSESS)

            # Phase 6: Gap Analysis
            gap_analysis = chat_utils.analyze_gaps(
                request.message, results, self.coverage_analyzer, self.recency_analyzer, self.coherence_analyzer
            )
            arches_controller.complete_stage(arches_session, PlanStage.ASSESS)

            if gap_analysis.coverage_gap or gap_analysis.recency_gap:
                arches_controller.set_flag(arches_session, "gap_detected", True)

            # Phase 7: Research Trigger
            research_trigger = request.enable_research and arches_controller.should_trigger_research(
                arches_session,
                {
                    "coverage_gap": gap_analysis.coverage_gap,
                    "coverage_score": gap_analysis.coverage_score,
                    "recency_gap": gap_analysis.recency_gap,
                },
            )
            
            research_summary = None
            if research_trigger:
                try:
                    research_summary = self._execute_research(
                        request, arches_controller, arches_session, gap_analysis, results
                    )
                    arches_controller.complete_stage(arches_session, PlanStage.RESEARCH)
                except Exception as e:
                    logger.error("research_execution_failed", error=str(e), exc_info=True)
                    # Don't fail the whole chat, just fallback?
                    # Or re-raise if critical? User wants to see 500?
                    # User likely wants a working system. Fallback is better.
                    # But let's re-raise for now to see the error in logs, but logging it explicitly guarantees we see it.
                    raise e
            
            # Phase 8: LLM Generation
            if not results:
                return self._handle_no_results(
                    conversation, request.message, request, gap_analysis,
                    is_strict, effective_grounding_level, conversation_block
                )

            system_prompt, user_prompt = build_llm_prompts(
                request.message, results, conversation_block, effective_grounding_level,
                persona=request.agent_persona
            )

            # Save user message
            user_message = Message(conversation_id=conversation.id, role="user", content=request.message)
            self.db.add(user_message)
            self.db.flush()

            try:
                llm_response = call_llm(
                    prompt=user_prompt,
                    system=system_prompt,
                    provider=request.provider,
                    max_tokens=request.max_tokens,
                )
            except Exception as exc:
                raise HTTPException(status_code=503, detail=f"LLM call failed: {exc}") from exc

            # Phase 9: Response Building
            from src.jarvis.controllers.chat_phases import build_chat_response
            return build_chat_response(
                self.db, conversation, request, llm_response, results,
                gap_analysis, effective_grounding_level, research_summary
            )
        except Exception as e:
            logger.error("process_chat_failed", error=str(e), exc_info=True)
            raise e
    def _handle_no_results(self, conversation, question, request, gap_analysis, is_strict, grounding_level, conversation_block):
        # Log User Message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=question,
        )
        self.db.add(user_message)
        self.db.flush()

        allow_creative = os.getenv("JARVIS_ALLOW_CREATIVE_FALLBACK", "").lower() in {"1", "true", "yes", "on"}
        
        if is_strict or not allow_creative:
            metadata = ChatMetadata(
                status="insufficient_context",
                grounding_level=grounding_level,
                gap_analysis=gap_analysis,
                research_enabled=request.enable_research,
                total_tokens=0, cost_usd=0.0
            )
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content="I could not find enough relevant context in memory to answer this yet.",
                token_count=0,
            )
            self.db.add(assistant_message)
            self.db.flush()
            return ChatResponse(
                conversation_id=conversation.id,
                message_id=assistant_message.id,
                query=question,
                response=None,
                sources=[],
                metadata=metadata,
            )

        # Creative Fallback
        creative_system = "You are JARVIS. No external memory available. Respond based on conversation history alone."
        creative_prompt = f"History:\n{conversation_block}\n\nUser: {question}\nAnswer:"
        
        response = call_llm(prompt=creative_prompt, system=creative_system, provider=request.provider, max_tokens=request.max_tokens)
        
        metadata = ChatMetadata(
            status="ok",
            llm_provider=response.provider,
            model=response.model,
            total_tokens=response.input_tokens + response.output_tokens,
            cost_usd=float(response.cost_usd),
            grounding_level=grounding_level,
            gap_analysis=gap_analysis,
            research_enabled=request.enable_research,
        )
        
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response.content,
            cost_usd=metadata.cost_usd,
            provider=metadata.llm_provider,
            model=metadata.model,
            token_count=metadata.total_tokens,
        )
        self.db.add(assistant_message)
        self.db.flush()
        
        return ChatResponse(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            query=question,
            response=response.content,
            sources=[],
            metadata=metadata,
        )
    def _execute_research(
        self,
        request: ChatRequest,
        arches_controller,
        arches_session,
        gap_analysis,
        results,
    ) -> ChatResearchSummary:
        """Execute research workflow with rate limiting and integration."""
        # Check rate limit before proceeding
        research_limiter = ResearchLimiter(self.research_limit_config)
        allowed, count = research_limiter.check_limit(request.user_id)
        if not allowed:
            logger.warning("research_rate_limited", user_id=request.user_id, current_count=count)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Hourly research limit reached ({count}/{self.research_limit_config.hourly_limit})"
            )

        arches_controller.set_flag(arches_session, "is_research_triggered", True)
        arches_controller.start_stage(arches_session, PlanStage.RESEARCH)
        
        # Execute Research
        # FIX: ResearchPlanner expects a dict, not a Pydantic model
        plan = self.planner.plan(request.message, gap_analysis.model_dump())
        research_results = self.executor.execute(plan)
        
        # Flatten results for integrator (expects strings)
        existing_text = [r.text for r in results]
        new_text = []
        for rr in research_results:
            for source in rr.sources:
                new_text.append(source.content)
                
        integration = self.integrator.integrate(request.message, existing_text, new_text)
        
        return ChatResearchSummary(
            triggered=True,
            reason=getattr(plan, 'reasoning', "gap_detected"),
            planned_queries=[q.query for q in plan.queries],
            executed_queries=len(research_results),
            sources_collected=sum(len(r.sources) for r in research_results),
            confidence_before=integration.confidence_before,
            confidence_after=integration.confidence_after,
            confidence_delta=integration.delta
        )
