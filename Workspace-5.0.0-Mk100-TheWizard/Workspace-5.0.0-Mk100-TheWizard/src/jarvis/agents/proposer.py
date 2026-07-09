import random
from typing import Dict, Any, Optional, List
from uuid import uuid4

from jarvis.governance.models import ProposalType
from jarvis.agents.base import BaseAgent
from jarvis.agents.reasoning_engine import ActionCandidate

class ProposerAgent(BaseAgent):
    """
    Agent responsible for introducing changes to the system.
    
    BMAD Strategy:
    - Conservative: Proposes stability measures when simulation variance is high.
    - Radical: Proposes upgrades when system is stagnant (low variance).
    """

    def observe(self, global_state: Dict[str, Any]):
        """Update internal beliefs based on observation."""
        self.memory.beliefs.update(global_state)
    
    def observe(self, global_state: Dict[str, Any]):
        """Update internal beliefs based on observation."""
        self.update_beliefs(global_state)
        self.current_step = global_state.get('step', 0)

    def update_beliefs(self, telemetry: Dict[str, Any]) -> Dict[str, float]:
        """Mathematical belief update."""
        var = telemetry.get('variance', 0.5)
        # Bounded update: System Stability = 1 - Variance
        self.memory.beliefs['system_stability'] = 1.0 - var
        # Potential for more complex math here (moving averages, etc.)
        return self.memory.beliefs

    def derive_goal(self) -> str:
        """Calculate ARGMAX(Belief * Value)."""
        u_stabilize = (1.0 - self.memory.beliefs.get('system_stability', 0.5)) * self.value_weights['stability']
        u_innovate = self.memory.beliefs.get('system_stability', 0.5) * self.value_weights['innovation']
        
        u_innovate_threshold = 0.3
        
        if u_stabilize > u_innovate_threshold: # Threshold
             if u_stabilize > u_innovate:
                 return "restore_stability"
        
        if u_innovate > 0.3:
            if u_innovate >= u_stabilize:
                return "foster_innovation"
                
        return "idle"

    
    def select_action(self, goal: str, candidates: List[ActionCandidate] = None) -> Optional[Dict[str, Any]]:
        """Map Goal + Candidates -> Final Action Spec."""
        if not candidates:
            return None
            
        # Filter Logic: In Phase 17-3, Math validates LLM suggestions
        # For now, we take the first valid candidate that matches the goal type
        
        for cand in candidates:
            if cand.action_type == "PROPOSAL":
                # Verify consistency (The "Constraint")
                # e.g., If goal is stability, parameters must relate to stability?
                # For V1, we trust the Mock/LLM but log the reasoning.
                return {
                    "title": cand.parameters["title"],
                    "description": cand.parameters["description"],
                    "type": ProposalType[cand.parameters["type"]], # Enum conversion
                    "domain": cand.parameters["domain"],
                    "reasoning": cand.reasoning,
                    "expected_effect": cand.expected_effect,
                    "confidence": cand.confidence
                }
        return None
    
    def decide_proposal(self, global_mean_trust: float, global_variance: float) -> Optional[Dict[str, Any]]:
        """Facade for Cognitive Pipeline."""
        # 1. Beliefs updated in observe() already
        
        # 2. Derive Goal (Math)
        active_goal = self.derive_goal()
        
        if active_goal == "idle":
            return None
            
        # 3. Reasoning (LLM/Mock)
        # Context includes specific metrics the LLM might need
        context = {
            "mean_trust": global_mean_trust,
            "variance": global_variance,
            "tier": self.tier
        }
        candidates = self.reasoning.suggest_actions(self.memory.beliefs, active_goal, context)
        
        # 4. Select Action (Math/Constraint)
        action = self.select_action(active_goal, candidates)
        
        if action:
            self.log_decision(active_goal, "PROPOSAL", action.get('reasoning', "N/A"), str(action.get('expected_effect', {})))
            del action['reasoning'] # Don't pass metadata to Proposal creation args if not needed
            del action['expected_effect']
            del action['confidence']
            
        return action


    def verify_outcome(self, proposal_id: str, outcome: str):
        # Basic Belief Update: If my proposal failed, maybe I am out of sync?
        # For V1: Just print or no-op logic.
        pass

