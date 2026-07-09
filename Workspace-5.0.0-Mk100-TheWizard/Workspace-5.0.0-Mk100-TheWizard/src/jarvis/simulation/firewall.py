"""Synthetic → evidence firewall (Story 11-7)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
import structlog

from jarvis.knowledge.tiers import KnowledgeTier
from jarvis.simulation.origins import OriginType

logger = structlog.get_logger(__name__)


class PromotionBlocked(Exception):
    """Raised when a forbidden promotion is attempted."""


@dataclass
class PromotionDecision:
    allowed: bool
    reason: str
    alert: Optional[str] = None


FORBIDDEN = {
    (OriginType.SYNTHETIC, KnowledgeTier.K0),
    (OriginType.SYNTHETIC, KnowledgeTier.K1),
    (OriginType.SYNTHETIC, KnowledgeTier.K2),
}


class SyntheticFirewall:
    """Hard gate preventing synthetic promotion to high tiers."""

    def __init__(self, cids=None, auditor=None) -> None:
        self.cids = cids
        self.auditor = auditor

    def validate_promotion(
        self,
        knowledge_id: str,
        from_tier: KnowledgeTier,
        to_tier: KnowledgeTier,
        origin: OriginType,
    ) -> PromotionDecision:
        if (origin, to_tier) in FORBIDDEN:
            reason = f"{origin.value} cannot promote to {to_tier.value}"
            self._notify(knowledge_id, origin, to_tier, reason)
            return PromotionDecision(False, reason, alert="synthetic_promotion_blocked")

        if origin == OriginType.SYNTHETIC and to_tier == KnowledgeTier.K3:
            # Allow provisional with label
            return PromotionDecision(True, "synthetic allowed to provisional with label")

        return PromotionDecision(True, "allowed")

    def enforce(self, knowledge_id: str, from_tier: KnowledgeTier, to_tier: KnowledgeTier, origin: OriginType) -> None:
        decision = self.validate_promotion(knowledge_id, from_tier, to_tier, origin)
        if not decision.allowed:
            raise PromotionBlocked(decision.reason)

    def _notify(self, knowledge_id: str, origin: OriginType, to_tier: KnowledgeTier, reason: str) -> None:
        logger.warning(
            "synthetic_promotion_attempt",
            knowledge_id=knowledge_id,
            origin=origin.value,
            to_tier=to_tier.value,
            reason=reason,
        )
        if self.cids:
            try:
                self.cids.events.append(
                    type(
                        "FirewallEvent",
                        (),
                        {"alert": True, "severity": "high", "patterns": ["synthetic_promotion"], "action": "deny"},
                    )()
                )
            except Exception:
                logger.warning("cids_notify_failed")
        if self.auditor:
            try:
                self.auditor.record({"knowledge_id": knowledge_id, "origin": origin.value, "target": to_tier.value, "reason": reason})
            except Exception:
                logger.warning("audit_notify_failed")
