"""Domain taxonomy validator.

Validates the domain heuristics for consistency, naming conventions,
and potential conflicts. Run this as a sanity check after modifying
domain mappings.

Usage:
    python -m jarvis.memory.validate_domains
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Set

import structlog

from jarvis.memory.domain_heuristics import CHAVAO_DOMAIN_MAP, DIRECT_DOMAIN_MAP, GD_KEYWORD_TAGS

logger = structlog.get_logger(__name__)


def validate_domain_hierarchy() -> bool:
    """Validate domain naming hierarchy and conventions.

    Rules:
    - Domain keys must use lowercase with underscores or dots
    - Hierarchical domains should use dot notation (e.g., "jarvis.memory")
    - No trailing/leading dots or underscores
    - Maximum 4 levels deep (e.g., "science.physics.quantum.qft" is too deep)

    Returns:
        True if all domains are valid, False otherwise.
    """
    all_domains: Set[str] = set()
    all_domains.update(DIRECT_DOMAIN_MAP.values())
    all_domains.update(CHAVAO_DOMAIN_MAP.values())
    # GD_KEYWORD_TAGS are tags, not domain keys, so skip

    invalid_domains: List[str] = []
    for domain in all_domains:
        # Check for valid characters (lowercase letters, digits, dots, underscores)
        if not all(c.islower() or c.isdigit() or c in "._" for c in domain):
            invalid_domains.append(f"{domain}: Contains invalid characters (use lowercase, digits, dots, underscores only)")
            continue

        # Check for leading/trailing dots or underscores
        if domain.startswith(".") or domain.startswith("_"):
            invalid_domains.append(f"{domain}: Starts with dot or underscore")
        if domain.endswith(".") or domain.endswith("_"):
            invalid_domains.append(f"{domain}: Ends with dot or underscore")

        # Check depth (max 3 levels, e.g., "jarvis.memory.rag")
        depth = domain.count(".") + 1
        if depth > 3:
            invalid_domains.append(f"{domain}: Too deep (max 3 levels, found {depth})")

    if invalid_domains:
        logger.error("domain_hierarchy_validation_failed", invalid_count=len(invalid_domains))
        for err in invalid_domains[:10]:  # Show first 10
            logger.error("invalid_domain", error=err)
        if len(invalid_domains) > 10:
            logger.error("additional_errors", count=len(invalid_domains) - 10)
        return False

    logger.info("domain_hierarchy_valid", total_domains=len(all_domains))
    return True


def check_keyword_conflicts() -> bool:
    """Check for conflicting keyword mappings.

    A conflict occurs when the same keyword maps to different domains
    across CHAVAO_DOMAIN_MAP and DIRECT_DOMAIN_MAP.

    Returns:
        True if no conflicts, False otherwise.
    """
    conflicts: List[str] = []

    # Check for overlaps between DIRECT_DOMAIN_MAP and CHAVAO_DOMAIN_MAP
    direct_keys = set(DIRECT_DOMAIN_MAP.keys())
    chavao_keys = set(CHAVAO_DOMAIN_MAP.keys())
    overlapping = direct_keys & chavao_keys

    for key in overlapping:
        if DIRECT_DOMAIN_MAP[key] != CHAVAO_DOMAIN_MAP[key]:
            conflicts.append(
                f"Keyword '{key}': DIRECT maps to '{DIRECT_DOMAIN_MAP[key]}' "
                f"but CHAVAO maps to '{CHAVAO_DOMAIN_MAP[key]}'"
            )

    if conflicts:
        logger.error("keyword_conflicts_found", conflict_count=len(conflicts))
        for conflict in conflicts:
            logger.error("keyword_conflict", conflict=conflict)
        return False

    logger.info("no_keyword_conflicts", total_keywords=len(CHAVAO_DOMAIN_MAP))
    return True


def analyze_domain_coverage() -> Dict[str, any]:
    """Analyze domain taxonomy coverage by category.

    Returns:
        Dictionary with coverage statistics.
    """
    all_domains = set(CHAVAO_DOMAIN_MAP.values())

    # Count domains by top-level category
    category_counts: Counter[str] = Counter()
    for domain in all_domains:
        top_level = domain.split(".")[0]
        category_counts[top_level] += 1

    # Calculate depth distribution
    depth_counts: Counter[int] = Counter()
    for domain in all_domains:
        depth = domain.count(".") + 1
        depth_counts[depth] += 1

    return {
        "total_unique_domains": len(all_domains),
        "total_keyword_mappings": len(CHAVAO_DOMAIN_MAP),
        "total_direct_mappings": len(DIRECT_DOMAIN_MAP),
        "total_gd_tags": len(GD_KEYWORD_TAGS),
        "category_distribution": dict(category_counts.most_common()),
        "depth_distribution": dict(sorted(depth_counts.items())),
    }


def validate_all() -> bool:
    """Run all validation checks.

    Returns:
        True if all validations pass, False otherwise.
    """
    logger.info("starting_domain_validation")

    hierarchy_valid = validate_domain_hierarchy()
    conflicts_valid = check_keyword_conflicts()

    # Analyze coverage (informational, always succeeds)
    coverage = analyze_domain_coverage()
    logger.info("domain_coverage_analysis", **coverage)

    # Print summary
    print("\n" + "=" * 80)
    print("DOMAIN TAXONOMY VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total unique domains: {coverage['total_unique_domains']}")
    print(f"Total keyword mappings: {coverage['total_keyword_mappings']}")
    print(f"Total direct mappings: {coverage['total_direct_mappings']}")
    print(f"Total GD tags: {coverage['total_gd_tags']}")
    print("\nTop categories:")
    for category, count in sorted(coverage['category_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {category}: {count} domains")
    print("\nDepth distribution:")
    for depth, count in coverage['depth_distribution'].items():
        print(f"  {depth} level(s): {count} domains")
    print("\nValidation results:")
    print(f"  [OK] Domain hierarchy: {'PASS' if hierarchy_valid else 'FAIL'}")
    print(f"  [OK] Keyword conflicts: {'PASS' if conflicts_valid else 'FAIL'}")
    print("=" * 80)

    return hierarchy_valid and conflicts_valid


if __name__ == "__main__":
    import sys

    success = validate_all()
    sys.exit(0 if success else 1)
