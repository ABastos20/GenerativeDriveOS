"""Trust Weight & Decay Engine (Story 11-5, Lock 7).

This module implements dynamic trust scoring with exponential decay.
Trust is not static - it evolves over time based on tier, usage, and contradictions.

Trust Dynamics Formula (AC #4):
    T(i,t) = c₀(i) · e^(-λ_K · (t - t₀))

Where:
- T(i,t) ∈ [0,1] = Trust at time t
- c₀(i) ∈ [0,1] = Initial confidence
- λ_K = Tier-dependent decay rate
- t₀ = Initial ingestion time
- t = Current time

Tier-Dependent Decay Rates:
| Tier | λ_K   | Half-life     |
|------|-------|---------------|
| K0   | 0     | ∞ (no decay)  |
| K1   | 10⁻⁶  | ~800 days     |
| K2   | 10⁻⁵  | ~80 days      |
| K3   | 10⁻³  | ~19 hours     |
| K4   | 10⁻²  | ~2 hours      |

References:
- [Story 11-5, AC #4: Trust Weight & Decay Engine]
- [Lock 7: Epistemic Sovereignty]
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from src.jarvis.knowledge.tiers import KnowledgeTier


# Tier-dependent decay rate constants (λ_K)
DECAY_RATES: dict[KnowledgeTier, float] = {
    KnowledgeTier.K0: 0.0,      # Ground truth - no decay
    KnowledgeTier.K1: 1e-6,     # Verified derivation - very slow decay
    KnowledgeTier.K2: 1e-5,     # Trust-scored external - slow decay
    KnowledgeTier.K3: 1e-3,     # Narrative - moderate decay
    KnowledgeTier.K4: 1e-2,     # Noise - fast decay
}

# Contradiction penalty range α ∈ [0.1, 0.5]
MIN_CONTRADICTION_PENALTY = 0.1
MAX_CONTRADICTION_PENALTY = 0.5

# Trust thresholds
MIN_TRUST_THRESHOLD = 0.01  # Below this, knowledge is archived
MAX_TRUST_CAP = 1.0  # Maximum trust value


@dataclass
class TrustState:
    """Current trust state of a knowledge unit.

    Attributes:
        knowledge_unit_id: ID of the knowledge unit
        current_trust: Current trust value T(i,t) ∈ [0,1]
        initial_confidence: Initial confidence c₀ ∈ [0,1]
        ingestion_time: Time of initial ingestion (t₀)
        last_refresh_time: Time of last trust refresh
        tier: Knowledge tier (determines decay rate)
        is_frozen: Whether unit is frozen due to arbitration
        contradiction_count: Number of contradictions encountered
    """
    knowledge_unit_id: UUID
    current_trust: float
    initial_confidence: float
    ingestion_time: datetime
    last_refresh_time: datetime
    tier: KnowledgeTier
    is_frozen: bool = False
    contradiction_count: int = 0

    def __post_init__(self):
        """Validate trust bounds."""
        if not 0.0 <= self.current_trust <= 1.0:
            raise ValueError(
                f"current_trust must be in [0, 1], got {self.current_trust}"
            )
        if not 0.0 <= self.initial_confidence <= 1.0:
            raise ValueError(
                f"initial_confidence must be in [0, 1], got {self.initial_confidence}"
            )


def calculate_trust(
    initial_confidence: float,
    tier: KnowledgeTier,
    ingestion_time: datetime,
    current_time: datetime,
) -> float:
    """Calculate trust value with exponential decay.

    Implements the core trust dynamics formula:
        T(i,t) = c₀(i) · e^(-λ_K · (t - t₀))

    Args:
        initial_confidence: Initial confidence c₀ ∈ [0,1]
        tier: Knowledge tier (determines λ_K)
        ingestion_time: Initial ingestion time (t₀)
        current_time: Current time (t)

    Returns:
        Trust value T(i,t) ∈ [0,1]

    Raises:
        ValueError: If initial_confidence out of bounds or current_time < ingestion_time
    """
    if not 0.0 <= initial_confidence <= 1.0:
        raise ValueError(f"initial_confidence must be in [0, 1], got {initial_confidence}")

    if current_time < ingestion_time:
        raise ValueError(
            f"current_time ({current_time}) cannot be before ingestion_time ({ingestion_time})"
        )

    # Get tier-dependent decay rate
    lambda_k = DECAY_RATES[tier]

    # Calculate time elapsed in seconds
    time_delta = (current_time - ingestion_time).total_seconds()

    # Apply exponential decay: T(i,t) = c₀ · e^(-λ_K · Δt)
    trust = initial_confidence * math.exp(-lambda_k * time_delta)

    # Clamp to [0, 1]
    return max(0.0, min(1.0, trust))


def calculate_trust_with_refresh(
    initial_confidence: float,
    tier: KnowledgeTier,
    ingestion_time: datetime,
    last_refresh_time: datetime,
    current_time: datetime,
) -> float:
    """Calculate trust value accounting for refresh events.

    When knowledge is verified/reused, trust refreshes: t₀ ← t
    This means we calculate decay from the last refresh time, not initial ingestion.

    Args:
        initial_confidence: Initial confidence c₀ ∈ [0,1]
        tier: Knowledge tier
        ingestion_time: Initial ingestion time
        last_refresh_time: Time of last refresh/verification
        current_time: Current time

    Returns:
        Trust value T(i,t) ∈ [0,1]
    """
    # Use last_refresh_time as effective t₀
    effective_t0 = max(ingestion_time, last_refresh_time)

    return calculate_trust(
        initial_confidence=initial_confidence,
        tier=tier,
        ingestion_time=effective_t0,
        current_time=current_time,
    )


def refresh_trust(state: TrustState, refresh_time: datetime) -> TrustState:
    """Refresh trust due to verification/reuse.

    Implements: t₀ ← t (reset decay clock)

    Args:
        state: Current trust state
        refresh_time: Time of verification/reuse event

    Returns:
        Updated trust state with refreshed time

    Raises:
        ValueError: If refresh_time < last_refresh_time
    """
    if refresh_time < state.last_refresh_time:
        raise ValueError(
            f"refresh_time ({refresh_time}) cannot be before "
            f"last_refresh_time ({state.last_refresh_time})"
        )

    # Calculate current trust before refresh
    current_trust = calculate_trust_with_refresh(
        initial_confidence=state.initial_confidence,
        tier=state.tier,
        ingestion_time=state.ingestion_time,
        last_refresh_time=state.last_refresh_time,
        current_time=refresh_time,
    )

    # Create new state with refreshed time
    return TrustState(
        knowledge_unit_id=state.knowledge_unit_id,
        current_trust=current_trust,
        initial_confidence=state.initial_confidence,
        ingestion_time=state.ingestion_time,
        last_refresh_time=refresh_time,  # t₀ ← t
        tier=state.tier,
        is_frozen=state.is_frozen,
        contradiction_count=state.contradiction_count,
    )


def apply_contradiction_penalty(
    state: TrustState,
    penalty_factor: float,
    contradicting_tier: Optional[KnowledgeTier] = None,
) -> TrustState:
    """Apply contradiction penalty to trust.

    Implements: T(i) ← α · T(i) where α ∈ [0.1, 0.5]

    Contradiction Resolution Rules:
    - If Tier(j) < Tier(i): Apply penalty (higher tier contradicts lower)
    - If Tier(j) = Tier(i): Freeze both (same tier conflict)
    - If Tier(j) > Tier(i): No penalty (lower tier can't contradict higher)

    Args:
        state: Current trust state
        penalty_factor: Penalty multiplier α ∈ [0.1, 0.5]
        contradicting_tier: Tier of contradicting knowledge (optional)

    Returns:
        Updated trust state with penalty applied

    Raises:
        ValueError: If penalty_factor not in [0.1, 0.5]
    """
    if not MIN_CONTRADICTION_PENALTY <= penalty_factor <= MAX_CONTRADICTION_PENALTY:
        raise ValueError(
            f"penalty_factor must be in [{MIN_CONTRADICTION_PENALTY}, "
            f"{MAX_CONTRADICTION_PENALTY}], got {penalty_factor}"
        )

    # Determine if penalty should be applied based on tier comparison
    should_apply_penalty = True
    should_freeze = False

    if contradicting_tier is not None:
        if contradicting_tier.trust_rank == state.tier.trust_rank:
            # Same tier: Freeze both (arbitration required)
            should_freeze = True
        elif contradicting_tier.trust_rank > state.tier.trust_rank:
            # Lower tier cannot contradict higher tier
            should_apply_penalty = False

    if not should_apply_penalty:
        return state

    # Apply penalty: T(i) ← α · T(i)
    penalized_trust = state.current_trust * penalty_factor

    return TrustState(
        knowledge_unit_id=state.knowledge_unit_id,
        current_trust=penalized_trust,
        initial_confidence=state.initial_confidence,
        ingestion_time=state.ingestion_time,
        last_refresh_time=state.last_refresh_time,
        tier=state.tier,
        is_frozen=should_freeze or state.is_frozen,
        contradiction_count=state.contradiction_count + 1,
    )


def should_archive(state: TrustState, current_time: datetime) -> bool:
    """Check if knowledge unit should be archived due to trust decay.

    Knowledge is archived when trust falls below minimum threshold.

    Args:
        state: Current trust state
        current_time: Current time for decay calculation

    Returns:
        True if trust < MIN_TRUST_THRESHOLD, False otherwise
    """
    current_trust = calculate_trust_with_refresh(
        initial_confidence=state.initial_confidence,
        tier=state.tier,
        ingestion_time=state.ingestion_time,
        last_refresh_time=state.last_refresh_time,
        current_time=current_time,
    )

    return current_trust < MIN_TRUST_THRESHOLD


def calculate_half_life(tier: KnowledgeTier) -> Optional[timedelta]:
    """Calculate half-life for a given tier.

    Half-life is the time for trust to decay to 50% of initial value.
    Formula: t₁/₂ = ln(2) / λ_K

    Args:
        tier: Knowledge tier

    Returns:
        timedelta representing half-life, or None if no decay (K0)
    """
    lambda_k = DECAY_RATES[tier]

    if lambda_k == 0:
        return None  # No decay, infinite half-life

    # t₁/₂ = ln(2) / λ_K
    half_life_seconds = math.log(2) / lambda_k

    return timedelta(seconds=half_life_seconds)


def calculate_time_to_threshold(
    state: TrustState,
    threshold: float,
    from_time: Optional[datetime] = None,
) -> Optional[timedelta]:
    """Calculate time until trust decays to threshold.

    Solves for t in: threshold = c₀ · e^(-λ_K · t)
    Result: t = -ln(threshold / c₀) / λ_K

    Args:
        state: Current trust state
        threshold: Target trust threshold
        from_time: Starting time (default: last_refresh_time)

    Returns:
        timedelta until threshold, or None if threshold unreachable
    """
    lambda_k = DECAY_RATES[state.tier]

    if lambda_k == 0:
        return None  # No decay

    if threshold >= state.initial_confidence:
        return None  # Already below threshold

    if threshold <= 0:
        return None  # Will never reach exactly 0

    # Solve: threshold = c₀ · e^(-λ_K · t)
    # t = -ln(threshold / c₀) / λ_K
    time_seconds = -math.log(threshold / state.initial_confidence) / lambda_k

    return timedelta(seconds=time_seconds)


def get_trust_cap_for_tier(tier: KnowledgeTier) -> float:
    """Get maximum trust cap for a given tier.

    Narrative knowledge (K3+) cannot exceed certain trust caps.
    This prevents over-reliance on unverified sources.

    Args:
        tier: Knowledge tier

    Returns:
        Maximum trust value for tier
    """
    caps = {
        KnowledgeTier.K0: 1.0,   # Ground truth - full trust possible
        KnowledgeTier.K1: 1.0,   # Verified derivation - full trust possible
        KnowledgeTier.K2: 0.95,  # Trust-scored external - high cap
        KnowledgeTier.K3: 0.75,  # Narrative - moderate cap
        KnowledgeTier.K4: 0.5,   # Noise - low cap
    }

    return caps[tier]


def enforce_trust_cap(trust: float, tier: KnowledgeTier) -> float:
    """Enforce tier-specific trust cap.

    Args:
        trust: Proposed trust value
        tier: Knowledge tier

    Returns:
        Trust value capped to tier maximum
    """
    cap = get_trust_cap_for_tier(tier)
    return min(trust, cap)
