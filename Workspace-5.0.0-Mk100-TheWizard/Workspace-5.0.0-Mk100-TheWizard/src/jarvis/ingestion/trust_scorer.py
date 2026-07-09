"""
Trust Scoring Engine for Sovereign Ingestion (Story 11-6).
Calculates credibility of ingested data based on provenance and integrity.

Integrates with Story 11-5's KnowledgeTier system.
"""
from dataclasses import dataclass
from typing import Dict, Optional
import hashlib

# Import 11-5's Knowledge Tier system
from jarvis.knowledge.tiers import (
    KnowledgeTier,
    SourceType,
    CollectionMethod,
    TierAssignmentContext,
    assign_tier,
)

@dataclass
class TrustScore:
    score: float  # 0.0 to 1.0
    tier: KnowledgeTier
    factors: Dict[str, float]
    recommendation: str

# Mapping from simple source_type strings to 11-5 SourceType enum
SOURCE_TYPE_MAP = {
    # K0: Ground Truth
    "sensor": SourceType.SENSOR,
    "telemetry": SourceType.TELEMETRY,
    "system_logs": SourceType.SYSTEM_LOGS,
    "on_device_metrics": SourceType.ON_DEVICE_METRICS,
    
    # K1: Verified Derivation
    "internal_analytics": SourceType.INTERNAL_ANALYTICS,
    "derived_model": SourceType.DERIVED_MODEL,
    "processed_metrics": SourceType.PROCESSED_METRICS,
    
    # K2: Trust-Scored External
    "research_paper": SourceType.PEER_REVIEWED_PAPER,
    "peer_reviewed": SourceType.PEER_REVIEWED_PAPER,
    "academic_book": SourceType.ACADEMIC_BOOK,
    "technical_standard": SourceType.TECHNICAL_STANDARD,
    "official_documentation": SourceType.OFFICIAL_DOCUMENTATION,
    
    # K3: Narrative
    "expert_blog": SourceType.BLOG_POST,
    "blog": SourceType.BLOG_POST,
    "news": SourceType.NEWS_ARTICLE,
    "expert_commentary": SourceType.EXPERT_COMMENTARY,
    "interview": SourceType.INTERVIEW,
    
    # K4: Noise
    "social": SourceType.SOCIAL_MEDIA,
    "social_media": SourceType.SOCIAL_MEDIA,
    "forum": SourceType.FORUM_POST,
    "web_scrape": SourceType.WEB_SCRAPE,
    "unknown": SourceType.UNVERIFIED_SOURCE,
}

class TrustScorer:
    """
    Evaluates data trustworthiness using 11-5's Knowledge Tier system.
    Uses assign_tier from jarvis.knowledge.tiers for deterministic assignment.
    """

    def score(self, content: str, metadata: Dict) -> TrustScore:
        source_type_str = metadata.get("source_type", "unknown")
        source_uri = metadata.get("source_uri", "unknown://origin")
        
        # 1. Map to 11-5 SourceType enum
        source_type = SOURCE_TYPE_MAP.get(source_type_str, SourceType.UNVERIFIED_SOURCE)
        
        # 2. Determine collection method (default to API_FETCH for external)
        collection_method = CollectionMethod.API_FETCH
        if source_type in (SourceType.SENSOR, SourceType.TELEMETRY, SourceType.ON_DEVICE_METRICS, SourceType.SYSTEM_LOGS):
            collection_method = CollectionMethod.DIRECT_CAPTURE
        elif source_type in (SourceType.PEER_REVIEWED_PAPER, SourceType.ACADEMIC_BOOK, SourceType.TECHNICAL_STANDARD):
            collection_method = CollectionMethod.DOCUMENT_PARSE
        elif source_type in (SourceType.SOCIAL_MEDIA, SourceType.FORUM_POST, SourceType.WEB_SCRAPE):
            collection_method = CollectionMethod.WEB_FETCH
            
        # 3. Integrity Check (Simple length/hash heuristic for now)
        integrity_mod = 1.0
        if not content:
            integrity_mod = 0.0
        elif len(content) < 10:
            integrity_mod = 0.5
        
        # 4. Create TierAssignmentContext and use 11-5's assign_tier
        context = TierAssignmentContext(
            source_type=source_type,
            collection_method=collection_method,
            origin=source_uri,
            initial_confidence=integrity_mod,
        )
        
        knowledge_tier = assign_tier(context)
        
        # 5. Calculate numeric score based on tier (for compatibility)
        tier_scores = {
            KnowledgeTier.K0: 1.0,
            KnowledgeTier.K1: 0.95,
            KnowledgeTier.K2: 0.80,
            KnowledgeTier.K3: 0.50,
            KnowledgeTier.K4: 0.20,
        }
        base_score = tier_scores.get(knowledge_tier, 0.10)
        final_score = base_score * integrity_mod
        
        # 6. Generate Recommendation
        recommendations = {
            KnowledgeTier.K0: "Ingest as Ground Truth",
            KnowledgeTier.K1: "Ingest as Verified Derivation",
            KnowledgeTier.K2: "Ingest as Trust-Scored External",
            KnowledgeTier.K3: "Ingest as Narrative (Low Priority)",
            KnowledgeTier.K4: "Quarantine - Noise",
        }
        rec = recommendations.get(knowledge_tier, "Quarantine - Unknown")
        
        return TrustScore(
            score=round(final_score, 2),
            tier=knowledge_tier,
            factors={
                "base": base_score,
                "integrity": integrity_mod,
            },
            recommendation=rec,
        )
