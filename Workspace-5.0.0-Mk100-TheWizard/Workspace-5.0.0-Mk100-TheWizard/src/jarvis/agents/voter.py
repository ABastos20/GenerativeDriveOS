import random
from typing import Dict, Any, List

from jarvis.governance.models import VoteChoice, Proposal
from jarvis.agents.base import BaseAgent
from jarvis.agents.reasoning_engine import ActionCandidate

class VoterAgent(BaseAgent):
    """
    Agent responsible for evaluating and voting on proposals.
    
    BMAD Strategy:
    - Trust-Based: Weights vote by proposer's reputation.
    - Alignment-Based: Checks if proposal domain matches own priorities.
    """

    def observe(self, global_state: Dict[str, Any]):
        """Update internal beliefs based on observation."""
        self.memory.beliefs.update(global_state)
    
    
    def observe(self, global_state: Dict[str, Any]):
        self.update_beliefs(global_state)
        self.current_step = global_state.get('step', 0)

    def update_beliefs(self, telemetry: Dict[str, Any]) -> Dict[str, float]:
        self.memory.beliefs.update(telemetry)
        return self.memory.beliefs

    def _derive_vote_goal(self, proposal: Proposal, proposer_trust: float) -> str:
        """
        Specialized goal derivation for Voting Context.
        Returns: "vote_for", "vote_against", "abstain"
        """
        # Utility Logic
        u_for = proposer_trust * self.value_weights['coherence']
        if proposal.description and "stability" in proposal.description.lower():
             u_for += 0.2 * self.value_weights['stability']
        
        u_against = (1.0 - proposer_trust) * self.value_weights['coherence']

        if u_for > u_against and u_for > 0.4:
            return "vote_for"
        elif u_against > u_for and u_against > 0.4:
            return "vote_against"
        return "abstain"

    def select_action(self, goal: str, candidates: List[ActionCandidate] = None) -> VoteChoice:
        if not candidates:
             return VoteChoice.ABSTAIN
             
        for cand in candidates:
            if cand.action_type == "VOTE":
                choice_str = cand.parameters.get("choice")
                if choice_str == "FOR": return VoteChoice.FOR
                if choice_str == "AGAINST": return VoteChoice.AGAINST
                
        return VoteChoice.ABSTAIN

    def decide_vote(self, proposal: Proposal, proposer_trust: float) -> VoteChoice:
        # 1. Update Contextual Beliefs
        self.update_trust(str(proposal.proposer_id), proposer_trust)
        
        # 2. Derive Goal (Contextual)
        active_goal = self._derive_vote_goal(proposal, proposer_trust)
        
        if active_goal == "abstain":
            return VoteChoice.ABSTAIN
            
        # 3. Reasoning
        candidates = self.reasoning.suggest_actions(self.memory.beliefs, active_goal, {})
        
        # 4. Select
        choice = self.select_action(active_goal, candidates)
        
        if choice != VoteChoice.ABSTAIN:
            # We assume reasoning is in the first candidate for logging
            reason = candidates[0].reasoning if candidates else "Math"
            self.log_decision(active_goal, choice.name, reason, "Alignment")
            
        return choice

    def verify_outcome(self, proposal_id: str, outcome: str):
        # Basic Belief Update: Did the majority agree with me?
        # Update CSI belief?
        pass

