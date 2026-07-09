from typing import List, Dict, Any
import statistics

from jarvis.agents.base import BaseAgent

class AnalystAgent(BaseAgent):
    """
    Agent responsible for observing global system health.
    
    BMAD Strategy:
    - Monitors CSI (Cognitive Stability Index).
    - Detects Trust Runaway (Consensus singularity).
    - Detects Fragmentation (High variance).
    """
    
    def compute_csi(self, trust_values: List[float]) -> float:
        """
        Compute Cognitive Stability Index (V1).
        
        CSI = 1.0 - (Normalized Variance of Trust / Max Possible Variance)
        
        Ideally:
        - CSI ~ 1.0: Perfect Consensus (Dangerous if total trust is low -> Stagnation? Or High -> Cult?)
        - actually, we want Healthy Variance.
        - Let's define CSI as stability of the *mechanism*, meaning variance is within bounds.
        
        For Phase 14 metric, Architect defined it as Inverse of Normalized Variance.
        """
        if not trust_values:
            return 0.0
            
        n = len(trust_values)
        if n < 2:
            return 1.0
            
        try:
            variance = statistics.variance(trust_values)
        except statistics.StatisticsError:
            return 0.0
            
        # Max variance for variable in [0,1] is 0.25 (half 0, half 1)
        normalized_variance = variance / 0.25
        
        # CSI = 1 - Normalized Variance
        # 1.0 = All same trust (High stability)
        # 0.0 = Max polarization (Half 0, Half 1)
        return max(0.0, 1.0 - normalized_variance)

    def observe(self, global_state: Dict[str, Any]):
        # Records history of CSI for trend analysis (Phase 17-3)
        pass

    def verify_outcome(self, proposal_id: str, outcome: str):
        # Analyst observes global effect of proposal on CSI
        pass

