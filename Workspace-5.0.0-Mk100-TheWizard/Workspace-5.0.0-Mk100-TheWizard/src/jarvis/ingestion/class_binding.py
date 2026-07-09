"""
Knowledge Class Binding (Story 11-6, AC5).
Validates declared knowledge class against inferred tier.
Detects and penalizes mismatches (e.g., "news" claiming "primary_evidence").
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple
import structlog

from jarvis.knowledge.tiers import KnowledgeTier, SourceType

logger = structlog.get_logger(__name__)


class DeclaredKnowledgeClass(str, Enum):
    """Knowledge classes that can be declared by data sources."""
    PRIMARY_EVIDENCE = "primary_evidence"      # Claims to be ground truth
    VERIFIED_ANALYSIS = "verified_analysis"    # Claims to be derived/verified
    EXPERT_OPINION = "expert_opinion"          # Claims to be expert-vetted
    GENERAL_INFORMATION = "general_information"  # Acknowledges narrative status
    UNVERIFIED = "unverified"                  # Acknowledges low trust


# Valid tier ranges for each declared class
VALID_TIERS_FOR_CLASS = {
    DeclaredKnowledgeClass.PRIMARY_EVIDENCE: {KnowledgeTier.K0},
    DeclaredKnowledgeClass.VERIFIED_ANALYSIS: {KnowledgeTier.K0, KnowledgeTier.K1},
    DeclaredKnowledgeClass.EXPERT_OPINION: {KnowledgeTier.K1, KnowledgeTier.K2},
    DeclaredKnowledgeClass.GENERAL_INFORMATION: {KnowledgeTier.K2, KnowledgeTier.K3, KnowledgeTier.K4},
    DeclaredKnowledgeClass.UNVERIFIED: {KnowledgeTier.K3, KnowledgeTier.K4},
}

# Source types that CANNOT claim certain classes
FORBIDDEN_CLAIMS = {
    # News sources cannot claim primary_evidence or verified_analysis
    SourceType.NEWS_ARTICLE: {DeclaredKnowledgeClass.PRIMARY_EVIDENCE, DeclaredKnowledgeClass.VERIFIED_ANALYSIS},
    SourceType.BLOG_POST: {DeclaredKnowledgeClass.PRIMARY_EVIDENCE, DeclaredKnowledgeClass.VERIFIED_ANALYSIS},
    SourceType.EXPERT_COMMENTARY: {DeclaredKnowledgeClass.PRIMARY_EVIDENCE},
    # Social media cannot claim anything above general_information
    SourceType.SOCIAL_MEDIA: {DeclaredKnowledgeClass.PRIMARY_EVIDENCE, DeclaredKnowledgeClass.VERIFIED_ANALYSIS, DeclaredKnowledgeClass.EXPERT_OPINION},
    SourceType.FORUM_POST: {DeclaredKnowledgeClass.PRIMARY_EVIDENCE, DeclaredKnowledgeClass.VERIFIED_ANALYSIS, DeclaredKnowledgeClass.EXPERT_OPINION},
    SourceType.WEB_SCRAPE: {DeclaredKnowledgeClass.PRIMARY_EVIDENCE, DeclaredKnowledgeClass.VERIFIED_ANALYSIS, DeclaredKnowledgeClass.EXPERT_OPINION},
    SourceType.UNVERIFIED_SOURCE: {DeclaredKnowledgeClass.PRIMARY_EVIDENCE, DeclaredKnowledgeClass.VERIFIED_ANALYSIS, DeclaredKnowledgeClass.EXPERT_OPINION},
}


@dataclass
class ClassBindingResult:
    """Result of knowledge class validation."""
    valid: bool
    declared_class: Optional[DeclaredKnowledgeClass]
    inferred_tier: KnowledgeTier
    final_tier: KnowledgeTier  # After any downgrade
    trust_penalty: float  # 0.0 = no penalty, 1.0 = full penalty (trust = 0)
    reason: str


class KnowledgeClassBinder:
    """
    Validates that ingested items' declared knowledge class matches their
    actual inferred tier. Mismatches trigger trust downgrades.
    
    Implements AC5: Knowledge Class Binding (11-5 Integration)
    """
    
    def validate(
        self,
        declared_class: Optional[str],
        source_type: SourceType,
        inferred_tier: KnowledgeTier,
    ) -> ClassBindingResult:
        """
        Validate declared knowledge class against source type and inferred tier.
        
        Args:
            declared_class: Optional declared knowledge class string
            source_type: The source type from ingestion
            inferred_tier: The tier assigned by trust scoring
            
        Returns:
            ClassBindingResult with validation outcome and any penalties
        """
        # If no class declared, no validation needed
        if not declared_class:
            return ClassBindingResult(
                valid=True,
                declared_class=None,
                inferred_tier=inferred_tier,
                final_tier=inferred_tier,
                trust_penalty=0.0,
                reason="No knowledge class declared",
            )
        
        # Parse declared class
        try:
            declared = DeclaredKnowledgeClass(declared_class)
        except ValueError:
            # Unknown class - treat as unverified
            logger.warning("unknown_knowledge_class", declared=declared_class)
            return ClassBindingResult(
                valid=False,
                declared_class=None,
                inferred_tier=inferred_tier,
                final_tier=KnowledgeTier.K4,  # Downgrade to noise
                trust_penalty=0.5,
                reason=f"Unknown knowledge class: {declared_class}",
            )
        
        # Check forbidden claims for source type
        forbidden = FORBIDDEN_CLAIMS.get(source_type, set())
        if declared in forbidden:
            # Mismatch: source cannot claim this class
            logger.warning(
                "class_binding_violation",
                source_type=source_type.value,
                declared=declared.value,
            )
            return ClassBindingResult(
                valid=False,
                declared_class=declared,
                inferred_tier=inferred_tier,
                final_tier=KnowledgeTier.K4,  # Force to noise tier
                trust_penalty=0.8,  # Severe penalty
                reason=f"Source type '{source_type.value}' cannot claim '{declared.value}'",
            )
        
        # Check if inferred tier is valid for declared class
        valid_tiers = VALID_TIERS_FOR_CLASS.get(declared, set())
        if inferred_tier not in valid_tiers:
            # Tier doesn't match declared class - apply moderate penalty
            logger.warning(
                "tier_class_mismatch",
                declared=declared.value,
                inferred_tier=inferred_tier.value,
                valid_tiers=[t.value for t in valid_tiers],
            )
            
            # Downgrade to highest valid tier for this class, or K4 if claiming too high
            if inferred_tier.trust_rank < min(t.trust_rank for t in valid_tiers):
                # Inferred tier is BETTER than what class allows - that's fine
                return ClassBindingResult(
                    valid=True,
                    declared_class=declared,
                    inferred_tier=inferred_tier,
                    final_tier=inferred_tier,
                    trust_penalty=0.0,
                    reason="Inferred tier exceeds class expectation (allowed)",
                )
            else:
                # Inferred tier is WORSE than declared class claims
                return ClassBindingResult(
                    valid=False,
                    declared_class=declared,
                    inferred_tier=inferred_tier,
                    final_tier=inferred_tier,  # Keep inferred (don't promote based on claims)
                    trust_penalty=0.3,  # Moderate penalty for overclaiming
                    reason=f"Declared class '{declared.value}' exceeds inferred tier '{inferred_tier.value}'",
                )
        
        # Valid binding
        return ClassBindingResult(
            valid=True,
            declared_class=declared,
            inferred_tier=inferred_tier,
            final_tier=inferred_tier,
            trust_penalty=0.0,
            reason="Knowledge class binding valid",
        )
