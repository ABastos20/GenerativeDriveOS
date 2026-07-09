"""Critical integration of existing vs newly researched knowledge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass
class IntegrationResult:
    summary: str
    conflicts: List[str]
    confidence_before: float
    confidence_after: float
    delta: float


class CriticalIntegrator:
    """Simple conflict detector and synthesizer.

    This is a heuristic implementation to gate research integration and can
    be enhanced with LLM reasoning in later iterations.
    """

    def __init__(self, base_confidence: float = 0.5) -> None:
        self.base_confidence = base_confidence

    def integrate(
        self,
        question: str,
        existing_chunks: Sequence[str],
        new_chunks: Sequence[str],
    ) -> IntegrationResult:
        conflicts: list[str] = []
        for old in existing_chunks:
            for new in new_chunks:
                if old and new and old.strip().lower() in new.strip().lower():
                    continue
                if old and new and new.strip().lower() in old.strip().lower():
                    continue
                if old and new and old.split()[:3] == new.split()[:3]:
                    conflicts.append(f"Potential divergence between '{old[:60]}' and '{new[:60]}'")

        confidence_after = min(1.0, self.base_confidence + 0.25 + 0.1 * len(new_chunks))
        delta = confidence_after - self.base_confidence
        summary_parts = [
            f"Question: {question}",
            f"New chunks integrated: {len(new_chunks)}",
            f"Conflicts detected: {len(conflicts)}",
        ]

        return IntegrationResult(
            summary=" | ".join(summary_parts),
            conflicts=conflicts,
            confidence_before=self.base_confidence,
            confidence_after=confidence_after,
            delta=delta,
        )

    def build_prompt(self, question: str, existing_chunks: Sequence[str], new_chunks: Sequence[str]) -> str:
        """Prompt template for old-vs-new comparison and synthesis."""
        existing_block = "\n\n".join(f"[Existing] {c}" for c in existing_chunks)
        new_block = "\n\n".join(f"[New] {c}" for c in new_chunks)
        return f"""
You are comparing existing knowledge against newly researched knowledge to detect conflicts and synthesize updates.

Question:
{question}

Existing knowledge:
{existing_block or 'None'}

Newly researched knowledge:
{new_block or 'None'}

Steps:
1) List conflicts or contradictions between existing and new knowledge (if any).
2) Identify what should be superseded and what should be preserved.
3) Provide a concise synthesis that maintains historical context.
4) Report confidence before/after integration and the delta.
"""
