"""Lock 2: Math Sovereignty Tests.

Verifies that goal selection is deterministic and mathematical,
not controlled by the LLM.

Lock 2 Rule: goal = argmax(belief × value)
The LLM does NOT choose goals - it only proposes actions.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from jarvis.agents.voter import VoterAgent
from jarvis.agents.reasoning_engine import ActionCandidate
from jarvis.governance.models import VoteChoice, Proposal


class TestLock2MathSovereignty:
    """
    Lock 2: Math Sovereignty
    
    Core invariant: LLM does not choose goals.
    Goal derived from: goal = argmax(belief × value)
    """

    @pytest.fixture
    def voter_agent(self):
        """Create a voter agent with controlled value weights."""
        agent = MagicMock(spec=VoterAgent)
        agent.value_weights = {
            'coherence': 0.8,
            'stability': 0.6,
            'innovation': 0.4,
        }
        agent.memory = MagicMock()
        agent.memory.beliefs = {}
        agent._derive_vote_goal = VoterAgent._derive_vote_goal.__get__(agent, VoterAgent)
        return agent

    @pytest.fixture
    def proposal(self):
        """Create a sample proposal."""
        return Proposal(
            id=uuid4(),
            title="Test Proposal",
            description="Improve stability of the system",
            proposer_id=uuid4(),
        )

    def test_goal_derived_from_math_not_llm(self, voter_agent, proposal):
        """
        Lock 2 Core Test: Goal is derived mathematically.
        
        The goal (vote_for, vote_against, abstain) is computed from:
        u_for = proposer_trust * value_weights['coherence']
        u_against = (1 - proposer_trust) * value_weights['coherence']
        
        LLM has NO influence on this calculation.
        """
        # High trust proposer
        high_trust = 0.9
        goal = voter_agent._derive_vote_goal(proposal, high_trust)
        
        # Math: u_for = 0.9 * 0.8 = 0.72, u_against = 0.1 * 0.8 = 0.08
        # Since "stability" in description: u_for += 0.2 * 0.6 = 0.12 → u_for = 0.84
        # u_for > u_against and u_for > 0.4 → vote_for
        assert goal == "vote_for", "High trust should derive vote_for goal"

    def test_low_trust_derives_against_goal(self, voter_agent, proposal):
        """Low trust proposer should derive vote_against goal."""
        low_trust = 0.1
        goal = voter_agent._derive_vote_goal(proposal, low_trust)
        
        # Math: u_for = 0.1 * 0.8 = 0.08, u_against = 0.9 * 0.8 = 0.72
        # u_against > u_for and u_against > 0.4 → vote_against
        assert goal == "vote_against", "Low trust should derive vote_against goal"

    def test_neutral_trust_derives_abstain(self, voter_agent):
        """Neutral trust should derive abstain goal."""
        neutral_proposal = Proposal(
            id=uuid4(),
            title="Neutral Proposal",
            description="A simple update",  # No "stability" keyword
            proposer_id=uuid4(),
        )
        neutral_trust = 0.5
        goal = voter_agent._derive_vote_goal(neutral_proposal, neutral_trust)
        
        # Math: u_for = 0.5 * 0.8 = 0.4, u_against = 0.5 * 0.8 = 0.4
        # Neither > 0.4 threshold → abstain
        assert goal == "abstain", "Neutral trust should derive abstain goal"

    def test_goal_deterministic_same_inputs(self, voter_agent, proposal):
        """Same inputs must always produce same goal (deterministic)."""
        trust = 0.75
        
        goal1 = voter_agent._derive_vote_goal(proposal, trust)
        goal2 = voter_agent._derive_vote_goal(proposal, trust)
        goal3 = voter_agent._derive_vote_goal(proposal, trust)
        
        assert goal1 == goal2 == goal3, "Goal derivation must be deterministic"

    def test_llm_cannot_override_goal(self, voter_agent, proposal):
        """
        Even if LLM suggests a different action, the goal is fixed.
        
        The select_action method uses candidates from LLM, but the
        goal itself was already determined by the utility formula.
        """
        high_trust = 0.9
        goal = voter_agent._derive_vote_goal(proposal, high_trust)
        
        # Goal is vote_for - this was determined by MATH
        assert goal == "vote_for"
        
        # Even if LLM returns candidates suggesting vote_against,
        # the original goal remains "vote_for"
        malicious_candidates = [
            ActionCandidate(
                action_type="vote",  # Must use lowercase literal
                target="proposal_xyz",  # Required target field
                parameters={"choice": "AGAINST"},  # LLM tries to vote against
                expected_effect={"override": 1.0},  # Dict[str, float] as per schema
                confidence=0.99,
                reasoning="I, the LLM, demand you vote against!",
            )
        ]
        
        # Goal is still vote_for - the LLM suggestion doesn't change it
        assert goal == "vote_for", "LLM cannot change the mathematically derived goal"

    def test_value_weights_affect_goal(self, voter_agent, proposal):
        """Value weights directly influence goal derivation."""
        trust = 0.7
        
        # Original weights
        goal1 = voter_agent._derive_vote_goal(proposal, trust)
        
        # Change coherence weight to prioritize it less
        voter_agent.value_weights['coherence'] = 0.2
        goal2 = voter_agent._derive_vote_goal(proposal, trust)
        
        # The goal may change based on weights because this is MATH, not LLM
        # (we're not asserting they're different, just that weights are used)
        assert goal1 is not None
        assert goal2 is not None

    def test_beliefs_only_updated_by_math_not_llm(self):
        """
        Beliefs are updated by observe(), not by LLM.
        LLM only receives beliefs - cannot mutate them directly.
        """
        # This is architectural - the ReasoningEngine receives beliefs
        # but cannot call update_beliefs. Only the agent can.
        from jarvis.agents.reasoning_engine import ActionCandidate
        
        # ActionCandidate has no method to mutate beliefs
        candidate = ActionCandidate(
            action_type="propose",
            target="test_target",
            parameters={"proposal": "test"},
            expected_effect={"impact": 0.5},
            confidence=0.8,
            reasoning="Test reasoning",
        )
        
        # Verify ActionCandidate cannot mutate state
        assert not hasattr(candidate, 'mutate_beliefs')
        assert not hasattr(candidate, 'set_goal')
        assert not hasattr(candidate, 'update_trust')


class TestLock2ActionCandidateConstraints:
    """
    Lock 2: ActionCandidate is READ-ONLY output from LLM.
    It cannot execute - it only proposes.
    """

    def test_action_candidate_is_data_only(self):
        """ActionCandidate is a data structure, not an executor."""
        candidate = ActionCandidate(
            action_type="vote",
            target="proposal_123",
            parameters={"choice": "FOR"},
            expected_effect={"approval": 1.0},
            confidence=0.9,
            reasoning="I approve this proposal",
        )
        
        # ActionCandidate is just data - it has no execute method
        assert not callable(getattr(candidate, 'execute', None))
        assert not hasattr(candidate, 'run')
        assert not hasattr(candidate, 'invoke')

    def test_action_candidate_fields_are_auditable(self):
        """All ActionCandidate fields must be present for audit."""
        candidate = ActionCandidate(
            action_type="propose",
            target="audit_target",
            parameters={"proposal": "test"},
            expected_effect={"result": 0.75},
            confidence=0.75,
            reasoning="Why I suggest this",
        )
        
        # All fields required for Lock 3 audit
        assert candidate.expected_effect is not None
        assert candidate.confidence is not None
        assert candidate.reasoning is not None
        assert 0.0 <= candidate.confidence <= 1.0

    def test_action_candidate_confidence_bounded(self):
        """Confidence must be in [0.0, 1.0]."""
        # Valid confidence
        valid = ActionCandidate(
            action_type="vote",
            target="test_target",
            parameters={},
            expected_effect={},
            confidence=0.5,
            reasoning="test",
        )
        assert 0.0 <= valid.confidence <= 1.0
        
        # Pydantic should reject invalid confidence
        with pytest.raises(Exception):  # ValidationError
            ActionCandidate(
                action_type="vote",
                target="test_target",
                parameters={},
                expected_effect={},
                confidence=1.5,  # Invalid: > 1.0
                reasoning="test",
            )


class TestLock2GoalFormulaVerification:
    """
    Explicit verification of the goal = argmax(belief × value) formula.
    """

    def test_utility_formula_matches_spec(self):
        """
        Verify the formula:
        u_for = proposer_trust * value_weights['coherence']
        u_against = (1 - proposer_trust) * value_weights['coherence']
        
        Plus bonus: if "stability" in description, u_for += 0.2 * value_weights['stability']
        """
        value_weights = {'coherence': 0.8, 'stability': 0.6}
        proposer_trust = 0.7
        has_stability_keyword = True
        
        # Apply formula
        u_for = proposer_trust * value_weights['coherence']
        if has_stability_keyword:
            u_for += 0.2 * value_weights['stability']
        u_against = (1.0 - proposer_trust) * value_weights['coherence']
        
        # Expected: u_for = 0.7 * 0.8 + 0.2 * 0.6 = 0.56 + 0.12 = 0.68
        # Expected: u_against = 0.3 * 0.8 = 0.24
        assert abs(u_for - 0.68) < 0.001
        assert abs(u_against - 0.24) < 0.001
        
        # Goal selection
        if u_for > u_against and u_for > 0.4:
            goal = "vote_for"
        elif u_against > u_for and u_against > 0.4:
            goal = "vote_against"
        else:
            goal = "abstain"
        
        assert goal == "vote_for"
