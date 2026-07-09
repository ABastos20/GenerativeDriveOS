"""Recursive self-training guard (Story 11-7)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional
import structlog

logger = structlog.get_logger(__name__)


class SelfTrainingViolation(Exception):
    """Raised when synthetic content is reused for training without waiver."""


@dataclass
class Waiver:
    granted_by: str
    reason: str
    signature: str


class SelfTrainingGuard:
    """Prevents synthetic outputs from being reused without governance waiver."""

    def __init__(self, auditor=None) -> None:
        self.auditor = auditor

    def detect_recursion(self, knowledge_id: str, ingestion_lineage: Iterable[str]) -> bool:
        return knowledge_id in set(ingestion_lineage or [])

    def validate(
        self,
        knowledge_id: str,
        ingestion_lineage: List[str],
        origin: str,
        waiver: Optional[Waiver] = None,
    ) -> None:
        if origin == "synthetic" and self.detect_recursion(knowledge_id, ingestion_lineage):
            if waiver is None:
                self._audit(knowledge_id, "blocked_recursive_training")
                raise SelfTrainingViolation("Synthetic output cannot be reused for training without waiver")
            self._audit(knowledge_id, "waived_recursive_training", waiver)

    def _audit(self, knowledge_id: str, event: str, waiver: Optional[Waiver] = None) -> None:
        logger.warning("self_training_guard", knowledge_id=knowledge_id, guard_event=event, waiver_present=bool(waiver))
        if self.auditor:
            try:
                self.auditor.record({"knowledge_id": knowledge_id, "event": event, "waiver": waiver})
            except Exception:
                logger.warning("self_training_audit_failed")
