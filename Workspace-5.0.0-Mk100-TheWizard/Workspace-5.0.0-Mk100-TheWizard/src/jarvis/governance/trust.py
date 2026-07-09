"""Trust Calculation Engine.

Story 9-3: Trust-Weighted Consensus.

This module implements the mathematical core of the meritocratic voting system.
It is responsible for:
1. Calculating raw Trust Scores (T) from components (E, C, H, R).
2. Deriving Voting Weight (w) from Trust, subject to constitutional constraints.

"Meritocracy tempered by constitutional limits."
"""

import math
from typing import List, Optional
import statistics

from jarvis.governance.models import GovernanceTrustScore, Constitution


class TrustCalculator:
    """Calculates trust scores and effective voting weights."""
    
    @staticmethod
    def calculate_raw_trust(score: GovernanceTrustScore, constitution: Constitution) -> float:
        """Calculate raw Trust Score ($T_i$) from components.
        
        Formula: T = w_E*E + w_C*C + w_H*H + w_R*R
        Weights are defined in the active Constitution.
        
        Args:
            score: TrustScore model instance containing components.
            constitution: Active Constitution model containing weights.
            
        Returns:
            Float between 0.0 and 1.0
        """
        trust = (
            (score.epistemic_reliability * constitution.weight_epistemic) +
            (score.governance_consistency * constitution.weight_consistency) +
            (score.historical_integrity * constitution.weight_integrity) +
            (score.reputation * constitution.weight_reputation)
        )
        return max(0.0, min(1.0, trust))

    @staticmethod
    def calculate_effective_weight(
        user_trust: float,
        population_weights: List[float],
        constitution: Constitution,
        apply_constraints: bool = True
    ) -> float:
        """Derive effective Voting Weight ($w_i$) from Trust ($T_i$).
        
        Applies Constitutional Safety Constraints defined in the Constitution:
        1. Sybil Resistance: Quadratic penalty for low trust (T < Sybil Threshold).
        2. Anti-Elite Capture: Cap at X * Median of population.
        3. Minority Floor: Minimum weight of epsilon.
        
        Args:
            user_trust: The raw trust score of the user (0.0-1.0).
            population_weights: List of ALL current active user weights (for median calc).
            constitution: Active Constitution model containing safety parameters.
            apply_constraints: Boolean to toggle constraints.
            
        Returns:
            Effective voting weight.
        """
        if not apply_constraints:
            return user_trust

        # 1. Sybil Resistance (The "Moat")
        # If Trust < Tau, apply quadratic penalty.
        weight = user_trust
        if user_trust < constitution.sybil_threshold:
            if constitution.sybil_threshold > 0:
                weight = (user_trust * user_trust) / constitution.sybil_threshold
            else:
                weight = user_trust
                
        # 2. Anti-Elite Capture (The "Ceiling")
        # Cannot exceed X * Median Weight.
        if population_weights:
            try:
                median_w = statistics.median(population_weights)
                # Failover for practically zero median
                if median_w < constitution.minority_floor:
                    median_w = constitution.minority_floor
                
                cap = median_w * constitution.anti_elite_multiplier
                weight = min(weight, cap)
            except statistics.StatisticsError:
                pass # Empty list handled by if check

        # 3. Minority Floor (The "Floor")
        # Voice cannot be completely silenced.
        weight = max(weight, constitution.minority_floor)
        
        return weight


class TrustUpdater:
    """Updates trust scores based on voting outcomes and activity.
    
    Story 9-3 AC 8-10: Trust Dynamics Update.
    
    Formula: T_new = T_old + η * Alignment
    - Aligned with passed outcome: +0.01
    - Voted against consensus: -0.01
    - Process abuse: -0.05
    - Inactivity decay: -0.01 per epoch without participation
    """
    
    # Learning rate for trust updates
    ETA_ALIGNED = 0.01        # Reward for voting with consensus
    ETA_DISSENT = -0.01       # Penalty for voting against consensus (mild)
    ETA_PROCESS_ABUSE = -0.05 # Penalty for process violations
    ETA_DECAY = -0.01         # Decay for inactivity per epoch
    
    @staticmethod
    def update_on_outcome(
        trust_score: GovernanceTrustScore,
        vote_aligned_with_outcome: bool,
        process_abuse: bool = False
    ) -> float:
        """Update trust score after a proposal resolves.
        
        AC 8: Update Equation T_new = T_old + η * Alignment
        
        Args:
            trust_score: The user's TrustScore model
            vote_aligned_with_outcome: True if user voted with the winning outcome
            process_abuse: True if user committed process violation
            
        Returns:
            New governance_consistency value (clamped to [0, 1])
        """
        current = trust_score.governance_consistency
        
        if process_abuse:
            delta = TrustUpdater.ETA_PROCESS_ABUSE
        elif vote_aligned_with_outcome:
            delta = TrustUpdater.ETA_ALIGNED
        else:
            delta = TrustUpdater.ETA_DISSENT
            
        new_value = max(0.0, min(1.0, current + delta))
        trust_score.governance_consistency = new_value
        
        return new_value
    
    @staticmethod
    def apply_inactivity_decay(trust_score: GovernanceTrustScore, epochs_inactive: int = 1) -> float:
        """Apply decay for inactivity.
        
        AC 9: Periodic decay for inactivity.
        
        Args:
            trust_score: The user's TrustScore model
            epochs_inactive: Number of epochs without participation
            
        Returns:
            New governance_consistency value (clamped to [0, 1])
        """
        current = trust_score.governance_consistency
        decay = TrustUpdater.ETA_DECAY * epochs_inactive
        
        new_value = max(0.0, min(1.0, current + decay))
        trust_score.governance_consistency = new_value
        
        return new_value
    
    @staticmethod
    def recenter_to_mean(trust_score: GovernanceTrustScore, population_mean: float = 0.5) -> float:
        """Re-center trust toward population mean (prevents runaway extremes).
        
        AC 9: Periodic re-centering.
        
        Formula: T_new = T_old + 0.1 * (mean - T_old)
        Move 10% closer to mean each epoch.
        
        Args:
            trust_score: The user's TrustScore model
            population_mean: Target mean (usually 0.5)
            
        Returns:
            New governance_consistency value
        """
        current = trust_score.governance_consistency
        delta = 0.1 * (population_mean - current)
        
        new_value = max(0.0, min(1.0, current + delta))
        trust_score.governance_consistency = new_value
        
        return new_value
