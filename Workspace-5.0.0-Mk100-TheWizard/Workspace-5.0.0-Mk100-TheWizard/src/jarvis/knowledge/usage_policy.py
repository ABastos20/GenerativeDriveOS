"""Knowledge Usage Policy Enforcement (Story 11-5, Lock 7).

This module enforces formal access control over which knowledge tiers
can be used for which purposes. This prevents narrative information
from influencing critical decisions like execution or governance.

Formal Rule (AC #5):
    Allowed(i, U) ⟺ Tier(i) ∈ U

Where:
- i = knowledge unit
- U = usage class with permitted tier set
- Tier(i) = knowledge tier of unit i

This is how the system prevents epistemic corruption in decision-making.

References:
- [Story 11-5, AC #5: Knowledge Usage Policy]
- [Lock 7: Epistemic Sovereignty]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID

from src.jarvis.knowledge.tiers import KnowledgeTier


class UsageClass(str, Enum):
    """Usage classes with different tier access requirements.

    Ordered from most restrictive to least restrictive.
    """
    EXECUTION_GUIDANCE = "execution_guidance"  # Code execution, tool use
    GOVERNANCE = "governance"                  # Governance decisions
    STRATEGY = "strategy"                      # Strategic planning
    IDEATION = "ideation"                      # Brainstorming, exploration
    RESEARCH = "research"                      # General research (alias for ideation)


# Default tier policy: Usage class → Allowed tiers
DEFAULT_USAGE_POLICY: dict[UsageClass, set[KnowledgeTier]] = {
    UsageClass.EXECUTION_GUIDANCE: {
        KnowledgeTier.K0,  # Ground truth only
        KnowledgeTier.K1,  # Verified derivation
    },
    UsageClass.GOVERNANCE: {
        KnowledgeTier.K0,
        KnowledgeTier.K1,
        KnowledgeTier.K2,  # Trust-scored external
    },
    UsageClass.STRATEGY: {
        KnowledgeTier.K0,
        KnowledgeTier.K1,
        KnowledgeTier.K2,
        KnowledgeTier.K3,  # Narrative
    },
    UsageClass.IDEATION: {
        KnowledgeTier.K0,
        KnowledgeTier.K1,
        KnowledgeTier.K2,
        KnowledgeTier.K3,
        KnowledgeTier.K4,  # Noise (all tiers)
    },
    UsageClass.RESEARCH: {  # Alias for ideation
        KnowledgeTier.K0,
        KnowledgeTier.K1,
        KnowledgeTier.K2,
        KnowledgeTier.K3,
        KnowledgeTier.K4,
    },
}


@dataclass
class UsagePolicyViolation:
    """Records a usage policy violation for audit trail.

    Attributes:
        knowledge_unit_id: ID of knowledge unit that violated policy
        tier: Tier of the knowledge unit
        usage_class: Attempted usage class
        allowed_tiers: Tiers allowed for this usage class
        context: Additional context about the violation
        reasoning_context: Optional reasoning engine context
    """
    knowledge_unit_id: UUID
    tier: KnowledgeTier
    usage_class: UsageClass
    allowed_tiers: set[KnowledgeTier]
    context: str
    reasoning_context: Optional[dict] = None

    @property
    def violation_summary(self) -> str:
        """Generate human-readable violation summary."""
        allowed_tier_names = ", ".join(sorted(t.value for t in self.allowed_tiers))
        return (
            f"Usage Policy Violation: Attempted to use {self.tier.value} knowledge "
            f"for {self.usage_class.value}, but only [{allowed_tier_names}] are permitted"
        )


@dataclass
class PolicyCheckResult:
    """Result of a usage policy check.

    Attributes:
        allowed: Whether the usage is permitted
        tier: Tier of the knowledge unit
        usage_class: Usage class being checked
        reason: Human-readable reason for decision
        violation: Optional violation details if not allowed
    """
    allowed: bool
    tier: KnowledgeTier
    usage_class: UsageClass
    reason: str
    violation: Optional[UsagePolicyViolation] = None


class KnowledgeUsagePolicy:
    """Knowledge usage policy enforcement engine.

    Implements AC #5: Enforce formal access control over knowledge usage.

    The policy defines which knowledge tiers can be used for which purposes,
    preventing narrative information (K3/K4) from influencing critical
    decisions like execution guidance or governance.
    """

    def __init__(
        self,
        policy: Optional[dict[UsageClass, set[KnowledgeTier]]] = None,
        enable_strict_mode: bool = True,
    ):
        """Initialize usage policy.

        Args:
            policy: Custom policy mapping (defaults to DEFAULT_USAGE_POLICY)
            enable_strict_mode: If True, violations raise exceptions
        """
        self.policy = policy or DEFAULT_USAGE_POLICY.copy()
        self.enable_strict_mode = enable_strict_mode
        self.violations: list[UsagePolicyViolation] = []

    def check_usage(
        self,
        knowledge_unit_id: UUID,
        tier: KnowledgeTier,
        usage_class: UsageClass,
        context: str = "",
    ) -> PolicyCheckResult:
        """Check if knowledge unit can be used for given purpose.

        Implements: Allowed(i, U) ⟺ Tier(i) ∈ U

        Args:
            knowledge_unit_id: ID of knowledge unit
            tier: Knowledge tier
            usage_class: Intended usage
            context: Additional context for audit trail

        Returns:
            PolicyCheckResult with decision and reasoning
        """
        allowed_tiers = self.policy.get(usage_class, set())

        # Formal rule: Allowed(i, U) ⟺ Tier(i) ∈ U
        is_allowed = tier in allowed_tiers

        if is_allowed:
            return PolicyCheckResult(
                allowed=True,
                tier=tier,
                usage_class=usage_class,
                reason=f"{tier.value} is permitted for {usage_class.value}",
                violation=None,
            )
        else:
            violation = UsagePolicyViolation(
                knowledge_unit_id=knowledge_unit_id,
                tier=tier,
                usage_class=usage_class,
                allowed_tiers=allowed_tiers,
                context=context,
            )

            # Record violation
            self.violations.append(violation)

            return PolicyCheckResult(
                allowed=False,
                tier=tier,
                usage_class=usage_class,
                reason=violation.violation_summary,
                violation=violation,
            )

    def check_usage_batch(
        self,
        knowledge_units: list[tuple[UUID, KnowledgeTier]],
        usage_class: UsageClass,
        context: str = "",
    ) -> list[PolicyCheckResult]:
        """Check multiple knowledge units at once.

        Args:
            knowledge_units: List of (id, tier) tuples
            usage_class: Intended usage
            context: Additional context

        Returns:
            List of PolicyCheckResult for each unit
        """
        return [
            self.check_usage(ku_id, tier, usage_class, context)
            for ku_id, tier in knowledge_units
        ]

    def filter_allowed_knowledge(
        self,
        knowledge_units: list[tuple[UUID, KnowledgeTier]],
        usage_class: UsageClass,
    ) -> list[UUID]:
        """Filter knowledge units to only those allowed for usage class.

        Args:
            knowledge_units: List of (id, tier) tuples
            usage_class: Intended usage

        Returns:
            List of knowledge unit IDs that pass policy check
        """
        allowed_tiers = self.policy.get(usage_class, set())
        return [ku_id for ku_id, tier in knowledge_units if tier in allowed_tiers]

    def get_allowed_tiers(self, usage_class: UsageClass) -> set[KnowledgeTier]:
        """Get allowed tiers for a usage class.

        Args:
            usage_class: Usage class to query

        Returns:
            Set of allowed tiers
        """
        return self.policy.get(usage_class, set()).copy()

    def update_policy(
        self,
        usage_class: UsageClass,
        allowed_tiers: set[KnowledgeTier],
        authorized_by: str,
    ) -> None:
        """Update usage policy (requires authorization).

        Args:
            usage_class: Usage class to update
            allowed_tiers: New set of allowed tiers
            authorized_by: Identity of authorizer

        Raises:
            ValueError: If policy update is invalid
        """
        # Validate that execution_guidance remains restrictive
        if usage_class == UsageClass.EXECUTION_GUIDANCE:
            if not allowed_tiers.issubset({KnowledgeTier.K0, KnowledgeTier.K1, KnowledgeTier.K2}):
                raise ValueError(
                    "EXECUTION_GUIDANCE cannot allow tiers beyond K2 (security constraint)"
                )

        # Validate that governance remains restrictive
        if usage_class == UsageClass.GOVERNANCE:
            if not allowed_tiers.issubset({KnowledgeTier.K0, KnowledgeTier.K1, KnowledgeTier.K2, KnowledgeTier.K3}):
                raise ValueError(
                    "GOVERNANCE cannot allow K4 (noise) tier (security constraint)"
                )

        # Update policy
        self.policy[usage_class] = allowed_tiers.copy()

    def get_violations(
        self,
        usage_class: Optional[UsageClass] = None,
        tier: Optional[KnowledgeTier] = None,
    ) -> list[UsagePolicyViolation]:
        """Get recorded violations with optional filtering.

        Args:
            usage_class: Filter by usage class (optional)
            tier: Filter by tier (optional)

        Returns:
            List of violations matching filters
        """
        violations = self.violations

        if usage_class is not None:
            violations = [v for v in violations if v.usage_class == usage_class]

        if tier is not None:
            violations = [v for v in violations if v.tier == tier]

        return violations

    def clear_violations(self) -> int:
        """Clear violation history.

        Returns:
            Number of violations cleared
        """
        count = len(self.violations)
        self.violations.clear()
        return count

    def get_usage_statistics(self) -> dict:
        """Get statistics on policy violations.

        Returns:
            Dictionary with violation statistics
        """
        if not self.violations:
            return {
                "total_violations": 0,
                "by_usage_class": {},
                "by_tier": {},
            }

        by_usage = {}
        by_tier = {}

        for v in self.violations:
            by_usage[v.usage_class.value] = by_usage.get(v.usage_class.value, 0) + 1
            by_tier[v.tier.value] = by_tier.get(v.tier.value, 0) + 1

        return {
            "total_violations": len(self.violations),
            "by_usage_class": by_usage,
            "by_tier": by_tier,
        }


class ConstitutionalDenial(Exception):
    """Exception raised when usage policy violation occurs in strict mode.

    This is a constitutional denial - the system refuses to proceed
    with an operation that would violate epistemic sovereignty.
    """

    def __init__(self, violation: UsagePolicyViolation):
        self.violation = violation
        super().__init__(violation.violation_summary)


def enforce_usage_policy(
    knowledge_unit_id: UUID,
    tier: KnowledgeTier,
    usage_class: UsageClass,
    policy: Optional[KnowledgeUsagePolicy] = None,
    context: str = "",
) -> PolicyCheckResult:
    """Enforce usage policy with optional exception on violation.

    Args:
        knowledge_unit_id: ID of knowledge unit
        tier: Knowledge tier
        usage_class: Intended usage
        policy: Policy engine (uses default if None)
        context: Additional context

    Returns:
        PolicyCheckResult

    Raises:
        ConstitutionalDenial: If strict mode enabled and violation occurs
    """
    if policy is None:
        policy = KnowledgeUsagePolicy(enable_strict_mode=True)

    result = policy.check_usage(knowledge_unit_id, tier, usage_class, context)

    if not result.allowed and policy.enable_strict_mode:
        raise ConstitutionalDenial(result.violation)

    return result


def get_most_restrictive_usage_for_tier(tier: KnowledgeTier) -> UsageClass:
    """Get most restrictive usage class that permits a given tier.

    Args:
        tier: Knowledge tier

    Returns:
        Most restrictive usage class that allows this tier
    """
    # Ordered from most restrictive to least
    usage_order = [
        UsageClass.EXECUTION_GUIDANCE,
        UsageClass.GOVERNANCE,
        UsageClass.STRATEGY,
        UsageClass.IDEATION,
    ]

    for usage_class in usage_order:
        if tier in DEFAULT_USAGE_POLICY[usage_class]:
            return usage_class

    # Should never reach here if all tiers are covered
    return UsageClass.IDEATION


def validate_policy_configuration(
    policy: dict[UsageClass, set[KnowledgeTier]]
) -> tuple[bool, list[str]]:
    """Validate that policy configuration is sound.

    Args:
        policy: Policy to validate

    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []

    # Check that all usage classes are present
    for usage_class in UsageClass:
        if usage_class not in policy:
            errors.append(f"Missing policy for {usage_class.value}")

    # Validate execution guidance is restrictive
    exec_tiers = policy.get(UsageClass.EXECUTION_GUIDANCE, set())
    if not exec_tiers.issubset({KnowledgeTier.K0, KnowledgeTier.K1, KnowledgeTier.K2}):
        errors.append("EXECUTION_GUIDANCE must not allow tiers > K2")

    # Validate governance doesn't allow noise
    gov_tiers = policy.get(UsageClass.GOVERNANCE, set())
    if KnowledgeTier.K4 in gov_tiers:
        errors.append("GOVERNANCE must not allow K4 (noise) tier")

    # Validate monotonicity: more permissive usage should allow all tiers from restrictive
    usage_hierarchy = [
        (UsageClass.EXECUTION_GUIDANCE, UsageClass.GOVERNANCE),
        (UsageClass.GOVERNANCE, UsageClass.STRATEGY),
        (UsageClass.STRATEGY, UsageClass.IDEATION),
    ]

    for restrictive, permissive in usage_hierarchy:
        restrictive_tiers = policy.get(restrictive, set())
        permissive_tiers = policy.get(permissive, set())

        if not restrictive_tiers.issubset(permissive_tiers):
            errors.append(
                f"{permissive.value} should allow all tiers from {restrictive.value} "
                "(monotonicity violation)"
            )

    return len(errors) == 0, errors
