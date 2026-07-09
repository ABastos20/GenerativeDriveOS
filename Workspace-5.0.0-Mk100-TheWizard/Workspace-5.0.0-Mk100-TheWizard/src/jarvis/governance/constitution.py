"""Constitutional Guard System.

Story 9-4: Constitutional Framework.

This module provides the "Supreme Court" layer of the governance system.
It enforces invariants that even the Owner cannot easily bypass without
a constitutional amendment.

Invariants Enforced:
1. Legitimacy Conservation Law: Total system mass cannot shift drastically.
2. Parameter Safety: Hard limits on dangerous governance parameters.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from jarvis.governance.models import Constitution

class ConstitutionalViolation(Exception):
    """Raised when an action violates the Supreme Law."""
    pass

class ConstitutionalGuard:
    
    @staticmethod
    def get_active_constitution(session: Session) -> Constitution:
        """Fetch the currently active Constitution.
        
        If none exists (bootstrap), returns a default in-memory one
        (or creates one if we want auto-bootstrap, but let's assume
        migration created one or we return a transient default).
        
        Actually, let's auto-create if missing to ensure system always has law.
        """
        stmt = select(Constitution).where(Constitution.active == True)
        constitution = session.execute(stmt).scalars().first()
        
        if not constitution:
            # Bootstrap default constitution if none exists
            constitution = Constitution(active=True)
            session.add(constitution)
            session.commit()
            session.refresh(constitution)
            
        return constitution

    @staticmethod
    def check_legitimacy_conservation(
        prev_total_weight: float,
        new_total_weight: float,
        max_drift: float
    ):
        """Enforce Legitimacy Conservation Law.
        
        The total voting mass of the system should not change by more than
        X% in a single update (epoch). This prevents "flash loan" attacks
        or massive sudden re-weightings.
        
        Args:
            prev_total_weight: Total weight before update.
            new_total_weight: Total weight after update.
            max_drift: Maximum allowed percentage change (0.0 - 1.0).
            
        Raises:
            ConstitutionalViolation if drift exceeded.
        """
        if prev_total_weight < 5.0:
            return # Bootstrap Phase: Allow unlimited growth until system stabilizes (approx 10 users)
            
        delta = abs(new_total_weight - prev_total_weight)
        pct_change = delta / prev_total_weight
        
        if pct_change > max_drift:
            raise ConstitutionalViolation(
                f"Legitimacy Conservation Violation: "
                f"Total weight drift {pct_change:.2%} exceeds constitutional limit {max_drift:.2%}."
            )

    @staticmethod
    def validate_parameter_safety(params: Dict[str, Any]):
        """Validate proposed constitutional parameters against hard safety limits.
        
        These are the "Eternity Clauses" - limits that presumably
        should never be crossed even by amendment (or require Code change).
        """
        # Check if we're updating trust weights - they must sum to 1.0
        weight_keys = ['weight_epistemic', 'weight_consistency', 'weight_integrity', 'weight_reputation']
        weight_params = {k: v for k, v in params.items() if k in weight_keys}
        
        if weight_params:
            # If any weights are updated, check their sum (assuming partial update needs all 4)
            if len(weight_params) == 4:
                total = sum(weight_params.values())
                if abs(total - 1.0) > 0.01:  # Allow small floating point error
                    raise ConstitutionalViolation(
                        f"Trust component weights must sum to 1.0, got {total:.3f}"
                    )
            
            # Check for negative weights
            for key, value in weight_params.items():
                if value < 0.0:
                    raise ConstitutionalViolation(f"Weights must be non-negative, {key}={value}")
        
        # Sybil threshold must be between 0.0 and 1.0
        if "sybil_threshold" in params:
            val = params["sybil_threshold"]
            if not (0.0 <= val <= 1.0):
                raise ConstitutionalViolation(
                    f"sybil_threshold must be between 0.0 and 1.0, got {val}"
                )
                
        # Minority floor must be positive but reasonable
        if "minority_floor" in params:
            val = params["minority_floor"]
            if val < 0.001:
                raise ConstitutionalViolation("Minority Floor cannot be effectively zero.")
            if val > 0.5:
                raise ConstitutionalViolation(f"Minority Floor too high: {val}")
                
        # Anti-Elite Cap cannot be removed (must be >= 1.0x median)
        if "anti_elite_multiplier" in params:
            val = params["anti_elite_multiplier"]
            if val < 1.0:
                raise ConstitutionalViolation("Anti-Elite Multiplier cannot be less than 1.0x Median.")
                
        # Max legitimacy drift must be reasonable
        if "max_legitimacy_drift" in params:
            val = params["max_legitimacy_drift"]
            if not (0.0 < val <= 1.0):
                raise ConstitutionalViolation(
                    f"max_legitimacy_drift must be between 0.0 and 1.0, got {val}"
                )
