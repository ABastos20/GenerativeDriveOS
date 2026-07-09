from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from uuid import UUID

from jarvis.agents.reasoning_engine import LLMReasoningEngine, ActionCandidate, MockProvider

@dataclass
class AgentMemory:
    """Local epistemic state of an agent."""
    beliefs: Dict[str, float] # Mathematical beliefs (0.0 to 1.0)
    goals: List[str]
    trust_cache: Dict[str, float]
    # Epistemic Audit Log
    decision_log: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.decision_log is None:
            self.decision_log = []

class BaseAgent(ABC):
    """Abstract base class for all cognitive agents."""
    
    def __init__(self, user_id: str, tier: int, initial_trust: float, reasoning_engine: Optional[LLMReasoningEngine] = None):
        self.user_id = user_id
        self.tier = tier
        self.trust = initial_trust
        self.memory = AgentMemory(beliefs={}, goals=[], trust_cache={})
        
        # The Brain (Defaults to Mock Provider within Engine if not provided)
        self.reasoning = reasoning_engine if reasoning_engine else LLMReasoningEngine(MockProvider())
        
        # DNA: Immutables values (0.0 to 1.0) defining the agent's core drive.
        # Derived from Tier for V1 simulation.
        self.value_weights: Dict[str, float] = self._derive_values()

    def _derive_values(self) -> Dict[str, float]:
        """Derive core values based on Tier Archetypes."""
        # Defaults
        values = {
            "stability": 0.5,
            "innovation": 0.5,
            "coherence": 0.5
        }
        if self.tier == 1: # Elders
            values = {"stability": 0.9, "innovation": 0.2, "coherence": 0.8}
        elif self.tier == 2: # Citizens
            values = {"stability": 0.4, "innovation": 0.8, "coherence": 0.6}
        elif self.tier == 3: # Noise
            values = {"stability": 0.1, "innovation": 0.9, "coherence": 0.1}
        return values

    def _sigmoid(self, x: float, k: float = 10.0, x0: float = 0.5) -> float:
        """Math helper for belief bounding (0-1)."""
        import math
        try:
            return 1 / (1 + math.exp(-k * (x - x0)))
        except OverflowError:
            return 0.0 if x < x0 else 1.0

    @abstractmethod
    def observe(self, global_state: Dict[str, Any]):
        """Update internal memory based on observations."""
        pass
        
    def update_beliefs(self, telemetry: Dict[str, Any]) -> Dict[str, float]:
        """
        Step 1: Update Beliefs (Must be mathematical).
        telemetry -> new_beliefs
        """
        # Default symbolic implementation available to subclasses
        return self.memory.beliefs

    def derive_goal(self) -> str:
        """
        Step 2: Derive Active Goal.
        argmax(belief * value_weights)
        """
        # Default symbolic implementation logic
        best_goal = "idle"
        
        # This logic interacts with subclass-specific goal definitions
        # So we might enforce subclasses to implement the specifics, 
        # but the signature is locked here.
        return best_goal
    
    @property
    def current_goal(self) -> str:
        """Return the most recent goal derived by the agent."""
        if self.memory.decision_log:
            return self.memory.decision_log[-1].get("active_goal", "unknown")
        return "idle"

    def select_action(self, goal: str) -> Optional[Dict[str, Any]]:
        """
        Step 3: Select Action.
        goal -> action_spec
        """
        return None

    def log_decision(self, goal: str, action: str, reason: str, expectation: str):
        """Structured logging for Epistemic Audit."""
        entry = {
            "step": getattr(self, "current_step", 0),
            "beliefs": self.memory.beliefs.copy(),
            "active_goal": goal,
            "action": action,
            "reason": reason,
            "expected_outcome": expectation
        }
        self.memory.decision_log.append(entry)
        # print(f"  🧠 [{self.user_id[:4]}] Goal: {goal} -> {action}")

    @abstractmethod
    def verify_outcome(self, proposal_id: str, outcome: str):
        """
        Cognitive Contract: VERIFY step.
        Agent observes the result of a proposal and updates beliefs matches/mismatches.
        """
        pass
    
    def update_trust(self, target_id: str, new_val: float):
        """Update local trust cache for a target."""
        self.memory.trust_cache[target_id] = new_val
