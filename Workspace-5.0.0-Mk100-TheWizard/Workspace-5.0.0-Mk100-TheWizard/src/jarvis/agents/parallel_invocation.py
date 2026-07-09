"""Async parallel invocation for Council of Ricks personas (Story 4.2).

Enhanced with memory attribution for Story 4.5.2:
- Build attributed context with chunk IDs
- Extract citations from agent responses
- Track per-agent memory usage
"""

import asyncio
import re
from typing import Any, Dict, List, Optional

import structlog

from jarvis.agents.personas import PersonaConfig
from jarvis.agents.response import MemoryAttribution, PersonaResponse

logger = structlog.get_logger(__name__)


def _build_attributed_context(
    context: str,
    chunks: Optional[List[Any]] = None,
) -> tuple[str, Dict[str, Any]]:
    """Build context string with chunk IDs for attribution tracking (Story 4.5.2).
    
    Adds chunk IDs in format [Source N | Chunk ID: xxx] so agent responses
    can be parsed to determine which chunks were actually cited.
    
    Args:
        context: Original RAG context string
        chunks: Optional list of chunk objects with id/metadata
        
    Returns:
        Tuple of (attributed_context_string, chunk_id_map)
        chunk_id_map maps source numbers to chunk metadata
    """
    if not chunks:
        # No chunks provided, return original context with empty map
        return context, {}
    
    chunk_id_map: Dict[str, Any] = {}
    attributed_parts = []
    
    for idx, chunk in enumerate(chunks, 1):
        # Extract chunk ID
        chunk_id = None
        if hasattr(chunk, "id"):
            chunk_id = str(chunk.id)
        elif hasattr(chunk, "point_id"):
            chunk_id = str(chunk.point_id)
        elif isinstance(chunk, dict) and "id" in chunk:
            chunk_id = str(chunk["id"])
        else:
            chunk_id = f"chunk_{idx}"
        
        # Extract metadata (domain, source, freshness)
        metadata = {}
        if hasattr(chunk, "metadata") and chunk.metadata:
            metadata = chunk.metadata if isinstance(chunk.metadata, dict) else {}
        elif isinstance(chunk, dict) and "metadata" in chunk:
            metadata = chunk.get("metadata", {})
        
        domain = metadata.get("primary_domain") or metadata.get("domain") or "unknown"
        source = metadata.get("doc_key") or metadata.get("source") or "unknown"
        freshness = metadata.get("freshness_score", 1.0)
        
        # Extract text content
        text = ""
        if hasattr(chunk, "text"):
            text = chunk.text
        elif isinstance(chunk, dict) and "text" in chunk:
            text = chunk.get("text", "")
        elif hasattr(chunk, "content"):
            text = chunk.content
        
        # Store in map for later attribution
        chunk_id_map[str(idx)] = {
            "chunk_id": chunk_id,
            "domain": domain,
            "source": source,
            "freshness": freshness,
        }
        
        # Build attributed source block
        attributed_parts.append(
            f"[Source {idx} | Chunk ID: {chunk_id}]\n{text.strip()}"
        )
    
    attributed_context = "\n\n".join(attributed_parts)
    
    logger.debug(
        "built_attributed_context",
        chunk_count=len(chunks),
        mapped_chunks=len(chunk_id_map),
    )
    
    return attributed_context, chunk_id_map


def _extract_used_chunks(
    content: str,
    chunk_id_map: Dict[str, Any],
) -> MemoryAttribution:
    """Parse agent response to extract which chunks were actually cited (Story 4.5.2).
    
    Uses regex to find citation patterns like [1], [Source 1], [Chunk ID: xxx]
    and maps them back to the original chunks.
    
    Args:
        content: Agent's response text
        chunk_id_map: Map from source numbers to chunk metadata
        
    Returns:
        MemoryAttribution with chunks_used, domains_accessed, sources, freshness
    """
    if not chunk_id_map:
        return MemoryAttribution(total_chunks_available=0)
    
    # Patterns to match citations:
    # [1], [2], etc. - simple numeric citations
    # [Source 1], [Source 2], etc. - explicit source refs
    # [Chunk ID: xxx] - direct chunk ID refs
    patterns = [
        r'\[(\d+)\]',  # [1], [2], etc.
        r'\[Source (\d+)\]',  # [Source 1], [Source 2]
        r'\[Chunk ID: ([^\]]+)\]',  # [Chunk ID: xxx]
    ]
    
    cited_sources = set()
    cited_chunk_ids = set()
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if match in chunk_id_map:
                # Numeric source reference
                cited_sources.add(match)
                cited_chunk_ids.add(chunk_id_map[match]["chunk_id"])
            else:
                # Might be a direct chunk ID
                for src_num, meta in chunk_id_map.items():
                    if meta["chunk_id"] == match:
                        cited_sources.add(src_num)
                        cited_chunk_ids.add(match)
    
    # Also check for implicit references (text matching chunks without explicit citation)
    # This is a heuristic - if chunk keywords appear in response, count as implicit use
    # For now, we only track explicit citations per performance constraints
    
    # Collect unique domains and sources from cited chunks
    domains_accessed = []
    sources = []
    freshness_values = []
    
    for src_num in cited_sources:
        if src_num in chunk_id_map:
            meta = chunk_id_map[src_num]
            if meta["domain"] not in domains_accessed:
                domains_accessed.append(meta["domain"])
            if meta["source"] not in sources:
                sources.append(meta["source"])
            freshness_values.append(meta.get("freshness", 1.0))
    
    # Calculate average freshness of cited chunks
    avg_freshness = sum(freshness_values) / len(freshness_values) if freshness_values else 0.0
    
    attribution = MemoryAttribution(
        chunks_used=list(cited_chunk_ids),
        domains_accessed=domains_accessed,
        sources=sources,
        memory_freshness=avg_freshness,
        total_chunks_available=len(chunk_id_map),
    )
    
    logger.debug(
        "extracted_chunk_citations",
        cited_count=len(cited_chunk_ids),
        total_available=len(chunk_id_map),
        domains=domains_accessed,
    )
    
    return attribution


async def invoke_persona_async(
    persona: PersonaConfig,
    context: str,
    query: str,
    provider: str = "auto",
    max_tokens: int = 2000,
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    chunk_id_map: Optional[Dict[str, Any]] = None,
) -> PersonaResponse:
    """Invoke a single persona asynchronously with LLM provider.

    Args:
        persona: Persona configuration (system prompt, weight, etc.)
        context: Retrieved RAG context to include in prompt
        query: User's original query
        provider: LLM provider to use ("auto" for smart routing)
        max_tokens: Maximum tokens in response
        max_retries: Number of retry attempts on failure
        initial_backoff: Initial backoff delay in seconds (doubles each retry)
        chunk_id_map: Optional map of source numbers to chunk metadata for attribution

    Returns:
        PersonaResponse with generated text and memory attribution
    """
    try:
        logger.info(
            "invoking_persona",
            persona_name=persona.name,
            weight=persona.weight,
            provider=provider
        )

        # Build prompt with persona's system prompt + context + query
        system_prompt = persona.system_prompt
        user_prompt = f"""Context from knowledge base:

{context}

---

Question: {query}

As {persona.name}, provide a thoughtful response based on the context above:"""

        # Retry logic with exponential backoff
        last_error = None
        backoff = initial_backoff
        
        for attempt in range(max_retries):
            try:
                # Run synchronous call_llm in thread pool to not block event loop
                import asyncio
                from functools import partial
                from jarvis.llm.client import call_llm
                
                loop = asyncio.get_event_loop()
                llm_response = await loop.run_in_executor(
                    None,  # Use default executor (ThreadPoolExecutor)
                    partial(
                        call_llm,
                        prompt=user_prompt,
                        system=system_prompt,
                        provider=provider,
                        max_tokens=max_tokens
                    )
                )
                
                # Extract memory attribution from response (Story 4.5.2)
                memory_attribution = None
                if chunk_id_map:
                    memory_attribution = _extract_used_chunks(
                        llm_response.content,
                        chunk_id_map,
                    )
                
                logger.info(
                    "persona_invocation_success",
                    persona_name=persona.name,
                    response_length=len(llm_response.content),
                    provider=llm_response.provider,
                    model=llm_response.model,
                    cost_usd=llm_response.cost_usd,
                    tokens=llm_response.input_tokens + llm_response.output_tokens,
                    chunks_cited=len(memory_attribution.chunks_used) if memory_attribution else 0,
                )

                return PersonaResponse(
                    persona=persona,
                    response_text=llm_response.content,
                    sources=[],  # Sources come from RAG, not LLM
                    error=None,
                    llm_provider=llm_response.provider,
                    llm_model=llm_response.model,
                    llm_cost_usd=llm_response.cost_usd,
                    llm_tokens=llm_response.input_tokens + llm_response.output_tokens,
                    memory_attribution=memory_attribution,
                )
                
            except Exception as retry_exc:
                last_error = retry_exc
                if attempt < max_retries - 1:
                    logger.warning(
                        "persona_invocation_retry",
                        persona_name=persona.name,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        backoff_seconds=backoff,
                        error=str(retry_exc)
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                else:
                    # Final retry failed
                    raise retry_exc

    except Exception as exc:
        logger.error(
            "persona_invocation_failed",
            persona_name=persona.name,
            error=str(exc),
            retries_exhausted=True
        )

        return PersonaResponse(
            persona=persona,
            response_text="",
            sources=[],
            error=exc,
            memory_attribution=None,
        )


async def invoke_personas_parallel(
    personas: List[PersonaConfig],
    context: str,
    query: str,
    provider: str = "auto",
    max_tokens: int = 2000,
    max_concurrent: int = 5,
    max_retries: int = 3,
    chunks: Optional[List[Any]] = None,
) -> List[PersonaResponse]:
    """Invoke multiple personas in parallel using asyncio with rate limiting.

    All personas share the same RAG context (no re-embedding per persona).
    Partial failures are handled gracefully - failed personas return error responses.
    Rate limiting prevents overwhelming LLM providers with too many concurrent requests.
    
    Story 4.5.2: When chunks are provided, attribution tracking is enabled.
    Each response will include which chunks the agent actually cited.

    Args:
        personas: List of persona configurations to invoke
        context: Shared RAG context retrieved once for all personas
        query: User's original query
        provider: LLM provider to use ("auto" for smart routing)
        max_tokens: Maximum tokens per response
        max_concurrent: Maximum number of concurrent LLM calls (rate limiting)
        max_retries: Number of retry attempts on failure
        chunks: Optional list of chunk objects for attribution tracking

    Returns:
        List of PersonaResponse objects with memory attribution
    """
    logger.info(
        "starting_parallel_invocation",
        persona_count=len(personas),
        persona_names=[p.name for p in personas],
        provider=provider,
        max_concurrent=max_concurrent,
        attribution_enabled=chunks is not None,
    )

    # Build attributed context if chunks provided (Story 4.5.2)
    attributed_context = context
    chunk_id_map: Dict[str, Any] = {}
    
    if chunks:
        attributed_context, chunk_id_map = _build_attributed_context(context, chunks)

    # Rate limiting: Use semaphore to limit concurrent LLM calls
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def rate_limited_invoke(persona: PersonaConfig) -> PersonaResponse:
        """Wrapper to invoke persona with rate limiting."""
        async with semaphore:
            return await invoke_persona_async(
                persona=persona,
                context=attributed_context,
                query=query,
                provider=provider,
                max_tokens=max_tokens,
                max_retries=max_retries,
                chunk_id_map=chunk_id_map,
            )

    # Create async tasks for all personas with rate limiting
    tasks = [rate_limited_invoke(persona) for persona in personas]

    # Gather with return_exceptions=True to handle partial failures
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert exceptions to error responses
    responses = []
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            # This shouldn't happen since invoke_persona_async catches exceptions,
            # but handle it just in case
            logger.error("unexpected_exception_in_parallel_invocation", error=str(result))
            responses.append(PersonaResponse(
                persona=personas[idx],
                response_text="",
                sources=[],
                error=result,
                memory_attribution=None,
            ))
        else:
            responses.append(result)

    success_count = sum(1 for r in responses if r.is_success)
    failure_count = len(responses) - success_count
    
    # Calculate total cost and tokens
    total_cost = sum(r.llm_cost_usd or 0.0 for r in responses if r.is_success)
    total_tokens = sum(r.llm_tokens or 0 for r in responses if r.is_success)
    
    # Attribution summary (Story 4.5.2)
    total_chunks_cited = sum(
        len(r.chunks_used) for r in responses if r.is_success
    )

    logger.info(
        "parallel_invocation_complete",
        total=len(responses),
        successes=success_count,
        failures=failure_count,
        total_cost_usd=round(total_cost, 4),
        total_tokens=total_tokens,
        total_chunks_cited=total_chunks_cited,
    )

    return responses
