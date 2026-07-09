"""Response data structures for parallel persona invocation.

Enhanced with memory attribution for Story 4.5.2:
- Track which chunks, domains, and sources each agent used
- Enable traceability of agent reasoning to specific documents
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.agents.personas import PersonaConfig


@dataclass
class MemoryAttribution:
    """Memory attribution data for an agent's response (Story 4.5.2).
    
    Tracks which memory chunks, domains, and sources an agent used
    to generate its response, enabling traceability of reasoning.
    
    Attributes:
        chunks_used: List of chunk IDs actually cited in response
        domains_accessed: List of domains the chunks come from
        sources: List of source document keys
        memory_freshness: Average freshness score of cited chunks (0.0-1.0)
        total_chunks_available: Total chunks in context (for comparison)
    """
    chunks_used: List[str] = field(default_factory=list)
    domains_accessed: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    memory_freshness: float = 0.0
    total_chunks_available: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "chunks_used": self.chunks_used,
            "domains_accessed": self.domains_accessed,
            "sources": self.sources,
            "memory_freshness": round(self.memory_freshness, 4),
            "total_chunks_available": self.total_chunks_available,
            "citation_rate": round(
                len(self.chunks_used) / max(self.total_chunks_available, 1), 2
            ),
        }


@dataclass
class PersonaResponse:
    """Response from a single persona invocation.

    Attributes:
        persona: The persona configuration that generated this response
        response_text: The generated response text
        sources: List of source citations (if applicable)
        error: Exception if the persona invocation failed, None if successful
        llm_provider: LLM provider used (e.g., "perplexity", "google-ai")
        llm_model: Model identifier
        llm_cost_usd: Cost in USD for this invocation
        llm_tokens: Total tokens (input + output)
        
        # Memory Attribution (Story 4.5.2)
        memory_attribution: Attribution data tracking chunk/domain/source usage
    """

    persona: PersonaConfig
    response_text: str
    sources: List[str]
    error: Optional[Exception] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_cost_usd: Optional[float] = None
    llm_tokens: Optional[int] = None
    
    # Memory Attribution (Story 4.5.2)
    memory_attribution: Optional[MemoryAttribution] = None

    @property
    def is_success(self) -> bool:
        """Check if invocation was successful."""
        return self.error is None
    
    # Convenience accessors for backward compatibility and ease of use
    @property
    def chunks_used(self) -> List[str]:
        """Chunk IDs actually cited in response."""
        return self.memory_attribution.chunks_used if self.memory_attribution else []
    
    @property
    def domains_accessed(self) -> List[str]:
        """Domains the cited chunks come from."""
        return self.memory_attribution.domains_accessed if self.memory_attribution else []
    
    @property
    def memory_freshness(self) -> float:
        """Average freshness score of cited chunks."""
        return self.memory_attribution.memory_freshness if self.memory_attribution else 0.0
