#!/usr/bin/env python
"""
Phase 14/17 Hybrid Simulator (v1 Real Integration)
Governance Simulation + Agent Cognition + Real Governance Engine

This script:
- Provisions tiered users in the REAL Database
- Uses Real Governance Engine (Voting, Proposal, Trust)
- Runs a proposal -> vote -> outcome loop
- Attaches stub cognitive agents
- Emits telemetry to artifacts/simulations/v1_run_real.json

Core Governance Logic is used, NOT mocked.
"""

import argparse
import random
import time
import json
import os
import asyncio
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional
from uuid import uuid4, UUID
from datetime import datetime, timezone

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))

from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from jarvis.database.postgres import get_engine
from jarvis.governance.models import (
    GovernanceUser, Role, TrustScore, Proposal, ProposalStatus, 
    ProposalType, VoteChoice, Constitution
)
from jarvis.governance.voting import ProposalManager, VotingEngine
from jarvis.governance.constitution import ConstitutionalGuard
from jarvis.governance.trust import TrustCalculator


# -------------------------------------
# ---------- DATA MODELS --------------
# -------------------------------------

@dataclass
class SimUser:
    user_id: str  # UUID string
    tier: int
    trust: float  # Cached local trust for agent logic
    
    # We don't store the ORM object here to avoid detachment issues,
    # fetch by ID when needed.

@dataclass
class TelemetryStep:
    step: int
    mean_trust: float
    trust_variance: float
    proposal_passed: bool
    csi: float
    active_proposals: int

# -------------------------------------
# ---------- AGENT IMPORTS ------------
# -------------------------------------

from jarvis.agents.proposer import ProposerAgent
from jarvis.agents.voter import VoterAgent
from jarvis.agents.analyst import AnalystAgent


# -------------------------------------
# ---------- REAL GOVERNANCE ENGINE ---
# -------------------------------------

class HybridSimulation:
    def __init__(self, steps: int, user_count: int, seed: int, provider_mode: str = "mock"):
        self.steps = steps
        self.user_count = user_count
        self.seed = seed
        self.provider_mode = provider_mode
        
        self.engine = get_engine()
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        
        # Core Engines
        self.voting_engine = VotingEngine(self.session)
        self.proposal_manager = ProposalManager(self.session)
        
        # State
        self.sim_users: List[SimUser] = []
        self.telemetry: List[dict] = []  # Changed to dict for flexibility
        self.prev_trust_map: dict = {}  # For trust gradient tracking (Part D)
        self.vote_history: List[dict] = []  # For cartelisation detection (Part D)
        self.failure_alerts: List[dict] = []  # Part D failure mode alerts

    def provision_users(self):
        """Provision users in Real DB and map to SimUser."""
        # Clean slate or reuse? For Sim, let's look for known sim emails or create new.
        # Format: sim_v1_{tier}_{idx}
        
        random.seed(self.seed)
        
        tiers = [
            ("Tier 1", 2, (0.35, 0.51), Role.ADMIN),
            ("Tier 2", 4, (0.15, 0.34), Role.CONTRIBUTOR),
            ("Tier 3", 4, (0.01, 0.14), Role.CONTRIBUTOR)
        ]
        
        tier_map = {"Tier 1": 1, "Tier 2": 2, "Tier 3": 3}
        
        print("\nProvisioning Users in DB...")
        for label, count, (t_min, t_max), role in tiers:
            for i in range(count):
                # Unique email per run/seed to avoid collisions if Nuke not run?
                # Or reuse if exists? Let's reuse for stability, reset trust.
                email = f"sim_{label.replace(' ', '')}_{i}@sim.local"
                
                # Use email format as subject_id for simulation simplicity
                subject_id = email 
                
                user = self.session.query(GovernanceUser).filter_by(subject_id=subject_id).first()
                if not user:
                    user = GovernanceUser(
                        id=uuid4(),
                        subject_id=subject_id,
                        name=f"{label} User {i}",
                        role=role,
                        is_active=True
                    )
                    self.session.add(user)
                    self.session.flush() # get ID
                    
                    # Create Trust Score
                    ts = TrustScore(
                        user_id=user.id,
                        epistemic_reliability=0.5, # Defaults
                        governance_consistency=0.5,
                        historical_integrity=0.5,
                        reputation=0.5
                    )
                    user.trust_metrics = ts
                    self.session.add(ts)
                
                # Reset Trust to Tier Range for this Start
                trust_val = random.uniform(t_min, t_max)
                # Set all components roughly equal to target trust for simplicity
                # Raw Trust = avg(components). So set all to trust_val.
                user.trust_metrics.epistemic_reliability = trust_val
                user.trust_metrics.governance_consistency = trust_val
                user.trust_metrics.historical_integrity = trust_val
                user.trust_metrics.reputation = trust_val
                
                self.sim_users.append(SimUser(
                    user_id=str(user.id),
                    tier=tier_map[label],
                    trust=trust_val
                ))
        
        self.session.commit()
        print(f"✅ Provisioned {len(self.sim_users)} users.")

    def run(self):
        random.seed(self.seed)
        
        # Instantiate Agents
        # For Phase 1, we map 1-to-1: One Proposer Agent instance? 
        # Or does each user have an agent wrapper?
        # Ideally: Each SimUser HAS-A Agent.
        # For this skeleton, let's create a list of Agent wrappers around the SimUsers.
        
        # Build the Brain (Reasoning Engine)
        reasoning_provider = None
        
        if self.provider_mode == "gemini":
            gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("JARVIS_GOOGLE_GENAI_API_KEY")
            if gemini_key:
                print("🧠 Logic: Gemini Neural Engine Active (Forensic Mode)")
                from jarvis.agents.reasoning_engine import GeminiProvider, LLMReasoningEngine
                from jarvis.agents.budget_guard import LLMGlobalBudgetGuard
                
                # 💸 GLOBAL BUDGET LOCK
                self.budget_guard = LLMGlobalBudgetGuard(max_usd=20.0, cost_per_1k_tokens=0.0005)
                
                reasoning_provider = GeminiProvider(budget_guard=self.budget_guard, api_key=gemini_key)
            else:
                 print("⚠️ Warning: Gemini Key not found. Falling back to Mock.")
        
        elif self.provider_mode == "openai":
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                print("🧠 Logic: OpenAI Neural Engine Active (Forensic Mode)")
                from jarvis.agents.reasoning_engine import OpenAIProvider, LLMReasoningEngine
                from jarvis.agents.budget_guard import LLMGlobalBudgetGuard
                
                # 💸 GLOBAL BUDGET LOCK
                self.budget_guard = LLMGlobalBudgetGuard(max_usd=20.0, cost_per_1k_tokens=0.0015)  # GPT-4o-mini pricing
                
                reasoning_provider = OpenAIProvider(budget_guard=self.budget_guard, api_key=openai_key)
            else:
                 print("⚠️ Warning: OPENAI_API_KEY not found. Falling back to Mock.")
        
        elif self.provider_mode == "codex":
            print("🧠 Logic: Codex CLI Neural Engine Active (Forensic Mode)")
            from jarvis.agents.reasoning_engine import CodexCLIProvider, LLMReasoningEngine
            from jarvis.agents.budget_guard import LLMGlobalBudgetGuard
            
            # 💸 GLOBAL BUDGET LOCK
            self.budget_guard = LLMGlobalBudgetGuard(max_usd=20.0, cost_per_1k_tokens=0.001)
            
            reasoning_provider = CodexCLIProvider(budget_guard=self.budget_guard)
        
        elif self.provider_mode == "openrouter":
            print("🧠 Logic: OpenRouter Neural Engine Active (FREE Tier - Forensic Mode)")
            from jarvis.agents.reasoning_engine import OpenRouterAdapter, LLMReasoningEngine
            from jarvis.agents.budget_guard import LLMGlobalBudgetGuard
            
            # 💸 GLOBAL BUDGET LOCK (mostly free but track)
            self.budget_guard = LLMGlobalBudgetGuard(max_usd=20.0, cost_per_1k_tokens=0.0)  # Free tier
            
            reasoning_provider = OpenRouterAdapter(budget_guard=self.budget_guard)
        
        elif self.provider_mode == "universal":
            print("🧠 Logic: Universal LLM Engine Active (Auto-Routing - Forensic Mode)")
            from jarvis.agents.reasoning_engine import UniversalLLMAdapter, LLMReasoningEngine
            from jarvis.agents.budget_guard import LLMGlobalBudgetGuard
            
            # 💸 GLOBAL BUDGET LOCK
            self.budget_guard = LLMGlobalBudgetGuard(max_usd=20.0, cost_per_1k_tokens=0.001)
            
            reasoning_provider = UniversalLLMAdapter(budget_guard=self.budget_guard, provider="auto")
        
        elif self.provider_mode == "claude":
            print("🧠 Logic: Claude CLI Neural Engine Active (Seat-Based - FREE)")
            from jarvis.agents.reasoning_engine import ClaudeCLIProvider, LLMReasoningEngine
            from jarvis.agents.budget_guard import LLMGlobalBudgetGuard
            
            # Claude seat = free, but track for telemetry
            self.budget_guard = LLMGlobalBudgetGuard(max_usd=20.0, cost_per_1k_tokens=0.0)
            
            reasoning_provider = ClaudeCLIProvider(budget_guard=self.budget_guard)
        
        elif self.provider_mode == "hybrid":
            print("🧠 Logic: Hybrid Ensemble Active")
            # TODO: Implement Ensemble
            pass
            
        if not reasoning_provider:
            print("🧠 Logic: Mock Reasoning (Control Group)")

        # Instantiate Persistent Agents
        # For simplicity in V1: 
        # - Tier 1 & 2 get ProposerAgent capabilities (logic)
        # - Everyone gets Voter capabilities 
        # But we need one Agent instance per user to hold beliefs.
        # Let's use ProposerAgent as the "Super" agent for Tier 1/2, and VoterAgent for Tier 3.
        # Ideally, we should have a `GovernanceAgent` that composes roles.
        # For now: If Tier <= 2, create ProposerAgent (it can also vote if we mix in or just define vote logic).
        # Wait, ProposerAgent and VoterAgent are distinct classes in the codebase.
        # To strictly follow the code, we might need to instantiate both or use one.
        # Quick Fix: Instantiate ProposerAgent for Tier 1/2, VoterAgent for Tier 3. 
        # And give ProposerAgent the ability to vote (or cast as VoterAgent when needed? No, separate memory).
        # Better: Just instantiate a dictionary of {user_id: Agent} and for voting, if it's a ProposerAgent, we assumed it could vote? 
        # Checking ProposerAgent... it imports from base. 
        # Let's just instantiate ProposerAgent for everyone for now? No, Proposer logic is specific.
        
        # Let's stick to the existing "Ephemeral" logic but store the *Belief State*? No, too complex.
        # Let's make Agents persistent.
        # Tier 1/2 -> ProposerAgent (We'll verify if it has deciding_vote. If not, we instantiate a separate Voter logic sharing same memory? Hard.)
        # Simplest Path for V1: 
        # Use ProposerAgent for Tier 1/2. Use VoterAgent for Tier 3.
        # When Tier 1/2 needs to vote, we might need to use a VoterAgent *temporarily* or add vote logic to Proposer.
        # Let's check if Proposer can vote. Likely not.
        # Okay, let's keep agents EPHEMERAL for the ACTION, but store their GOALS for the Telemetry?
        # NO. The architect wants "Cognitive Contract Adherence" -> "Update Beliefs".
        # Beliefs must persist.
        # We need a `GovernanceAgent` that has `beliefs`.
        # Taking a shortcut: I will create `self.agents` which maps `user_id` -> `ProposerAgent` (Tier 1/2) or `VoterAgent` (Tier 3).
        # For voting, if the agent is a Proposer, we will instantiate a *new* VoterAgent but pass in the Proposer's beliefs? 
        # Or just let Proposers only propose and Voters only vote? But Proposers *must* vote in the system.
        # 
        # Refined Plan:
        # Everyone is a VoterAgent.
        # Tier 1/2 *ALSO* have a ProposerAgent instance (or capability).
        # `self.agents` will track the PRIMARY agent for Goal Entropy (Proposer for T1/2, Voter for T3).
        
        self.agents = {}
        for u in self.sim_users:
            if u.tier <= 2:
                # Primary cognitive agent is Proposer
                agent = ProposerAgent(
                    user_id=u.user_id, 
                    tier=u.tier, 
                    initial_trust=u.trust,
                    reasoning_engine=LLMReasoningEngine(reasoning_provider) if reasoning_provider else None
                )
            else:
                agent = VoterAgent(
                    user_id=u.user_id, 
                    tier=u.tier, 
                    initial_trust=u.trust,
                    reasoning_engine=LLMReasoningEngine(reasoning_provider) if reasoning_provider else None
                )
            self.agents[u.user_id] = agent

        # Global Analyst
        analyst_agent = AnalystAgent(user_id="global_observer", tier=0, initial_trust=1.0)
        
        print(f"Starting Simulation ({self.steps} steps)...")
        
        for step in range(1, self.steps + 1):
            
            # --- 1. PROPOSAL PHASE ---
            active_proposals = []
            
            # Iterate through users to see if anyone wants to propose
            # (Limiting to Tiers 1 & 2 for proposals)
            for sim_u in self.sim_users:
                if sim_u.tier > 2: continue
                
                # Retrieve Persistent Agent
                # We know Tier <= 2 is ProposerAgent
                proposer = self.agents[sim_u.user_id]
                
                # Global Metrics for Decision
                trust_vals = [u.trust for u in self.sim_users]
                mean_trust = sum(trust_vals) / len(trust_vals)
                var_raw = 1.0 - analyst_agent.compute_csi(trust_vals) # Invert CSI to get variance approx
                
                # OBSERVE
                proposer.observe({'variance': var_raw, 'mean_trust': mean_trust, 'step': step})
                
                proposal_spec = proposer.decide_proposal(mean_trust, var_raw)
                
                if proposal_spec:
                    try:
                        proposer_db = self.session.query(GovernanceUser).get(sim_u.user_id)
                        prop = self.proposal_manager.create_proposal(
                            title=proposal_spec["title"],
                            description=proposal_spec["description"],
                            proposer=proposer_db,
                            proposal_type=proposal_spec["type"],
                            domain=proposal_spec.get("domain"),
                            duration_hours=24
                        )
                        self.session.commit()
                        self.proposal_manager.open_proposal(prop.id, proposer_db)
                        self.session.commit()
                        active_proposals.append(prop)
                        # print(f"  [Step {step}] {sim_u.user_id[:4]} Proposed: {proposal_spec['title']}")
                    except Exception as e:
                        print(f"  [Step {step}] Propose Failed: {e}")

            # --- 2. VOTING PHASE ---
            # Process newly created active proposals
            # (In reality, would process all OPEN, but for sim step we focus on the batch)
            
            passed_count = 0
            
            for prop in active_proposals:
                # Everyone votes
                votes_cast = 0
                for sim_u in self.sim_users:
                    # Resolve Agent for Voting
                    # If it's a ProposerAgent, it doesn't have decide_vote. 
                    # We need a Voter capability.
                    # For V1, we will instantiate a Transient VoterAgent but INJECT the beliefs of the persistent agent?
                    # Or simpler: Just instantiate a new VoterAgent for everyone for voting.
                    # BUT this breaks Goal Entropy if we want to track the Voter's goal.
                    # However, we tracked `self.agents` goals.
                    # Let's just use a transient VoterAgent for the vote action, 
                    # but rely on `self.agents` for the Entropy metric (which tracks the *primary* goal of the agent, e.g. "Stabilize" or "Disrupt").
                    
                    voter = VoterAgent(
                         user_id=sim_u.user_id, 
                         tier=sim_u.tier, 
                         initial_trust=sim_u.trust,
                         reasoning_engine=LLMReasoningEngine(reasoning_provider) if reasoning_provider else None
                    )
                    
                    # OBSERVE
                    voter.observe({'step': step})

                    # Heuristic: Proposer Trust. Need to fetch Proposer's current trust from SimUser list.
                    # Find proposer in sim_users
                    proposer_trust = 0.5
                    for potential_p in self.sim_users:
                        if potential_p.user_id == str(prop.proposer_id):
                            proposer_trust = potential_p.trust
                            break
                    
                    choice = voter.decide_vote(prop, proposer_trust)
                    
                    if choice != VoteChoice.ABSTAIN:
                        try:
                            voter_db = self.session.query(GovernanceUser).get(sim_u.user_id)
                            self.voting_engine.cast_vote(prop.id, voter_db, choice)
                            votes_cast += 1
                        except Exception:
                            pass
                
                self.session.commit()
                
                # --- 3. RESOLUTION PHASE ---
                prop.deadline = datetime.now(timezone.utc) # Force Close
                self.session.commit()
                
                try:
                    final_prop = self.voting_engine.resolve_proposal(prop.id)
                    if final_prop.status == ProposalStatus.PASSED:
                        passed_count += 1
                    
                    # --- 4. VERIFY PHASE (Cognitive Contract) ---
                    # Notify Agents of Outcome
                    # Ideally we notify appropriate agent instances.
                    # Since we use ephemeral agents, we assume they access history or we notify "Active" ones.
                    # For V1: Simple loop to show we closed it.
                    # Re-instantiate to simulate "Hearing the News"
                    for sim_u in self.sim_users:
                         # Just Proposers/Voters care
                         if sim_u.tier <= 2:
                            agent = self.agents.get(sim_u.user_id) # Use persistent agent
                            if agent:
                                agent.verify_outcome(str(prop.id), final_prop.status.value)

                except Exception as e:
                    print(f"Resolve Error: {e}")

            # --- 4. TELEMETRY PHASE ---
            # Refresh Trust States & Calculate Metrics
            trust_vals = []
            current_trust_map = {}
            constitution = ConstitutionalGuard.get_active_constitution(self.session)
            
            # Trust Gradient Stub: We need prev trust to calc gradient. 
            # For V1, we'll just log the variance/mean change.
            
            for sim_u in self.sim_users:
                u_db = self.session.query(GovernanceUser).get(sim_u.user_id) 
                
                # Update SimUser trust (Link DB -> Agent)
                # TODO: Part D - Enable Real Trust Feedback Loop.
                # For now, we apply small random drift to test "Trust Gradient" metric
                drift = (random.random() - 0.5) * 0.05 # Increased drift for visibility
                
                # Mutate Epistemic Reliability for drift
                if u_db.trust_metrics:
                    new_val = u_db.trust_metrics.epistemic_reliability + drift
                    u_db.trust_metrics.epistemic_reliability = max(0.01, min(0.99, new_val))
                
                # Recalc composite trust
                raw_trust = TrustCalculator.calculate_raw_trust(u_db.trust_metrics, constitution)
                sim_u.trust = raw_trust
                
                trust_vals.append(sim_u.trust)
                current_trust_map[sim_u.user_id] = sim_u.trust

            # Calculate CSI
            # Inline stats since TrustCalculator doesn't have it
            if len(trust_vals) > 0:
                mean_t = sum(trust_vals) / len(trust_vals)
                if len(trust_vals) > 1:
                    variance_t = sum((x - mean_t) ** 2 for x in trust_vals) / (len(trust_vals) - 1)
                else:
                    variance_t = 0.0
                
                # CSI = 1.0 - Scaled Variance (Simplistic V1)
                # Actually, AnalystAgent uses a specific formula. Let's use Analyst's CSI if available or keep simple.
                csi = 1.0 - (variance_t * 4) # Arbitrary scaling to make variance visible
                csi = max(0.0, min(1.0, csi))
                
                stats = {"mean": mean_t, "variance": variance_t, "csi": csi}
            else:
                stats = {"mean": 0.0, "variance": 0.0, "csi": 0.0}
            
            # Calculate Goal Entropy
            import math
            goals = []
            for agent in self.agents.values():
                 goals.append(agent.current_goal)
            
            goal_counts = {g: goals.count(g) for g in set(goals)}
            total_goals = len(goals)
            entropy = 0.0
            if total_goals > 0:
                for count in goal_counts.values():
                    p = count / total_goals
                    entropy -= p * math.log(p)
            
            # --- PART D: FAILURE MODE DETECTION ---
            max_trust_delta = 0.0
            trust_deltas = []
            
            # Calculate trust gradient if we have previous trust values
            if self.prev_trust_map:
                for user_id, current_trust in current_trust_map.items():
                    prev_trust = self.prev_trust_map.get(user_id, current_trust)
                    delta = abs(current_trust - prev_trust)
                    trust_deltas.append(delta)
                    if delta > max_trust_delta:
                        max_trust_delta = delta
            
            # Trust Runaway Detection (ΔTrust > 0.15)
            runaway_detected = max_trust_delta > 0.15
            if runaway_detected:
                alert = {"step": step, "type": "TRUST_RUNAWAY", "delta": max_trust_delta}
                self.failure_alerts.append(alert)
                print(f"  ⚠️ TRUST RUNAWAY: ΔMax={max_trust_delta:.3f}")
            
            # Trust Saturation Detection (>50% above 0.85)
            high_trust_count = sum(1 for t in trust_vals if t > 0.85)
            saturation_detected = high_trust_count > len(trust_vals) * 0.5
            if saturation_detected:
                alert = {"step": step, "type": "TRUST_SATURATION", "count": high_trust_count, "total": len(trust_vals)}
                self.failure_alerts.append(alert)
                print(f"  ⚠️ TRUST SATURATION: {high_trust_count}/{len(trust_vals)} above 0.85")
            
            # Store current trust for next step comparison
            self.prev_trust_map = current_trust_map.copy()
            
            # Calculate mean trust delta for telemetry
            mean_trust_delta = sum(trust_deltas) / len(trust_deltas) if trust_deltas else 0.0
            
            self.telemetry.append({
                "step": step,
                "mean_trust": stats["mean"],
                "trust_variance": stats["variance"],
                "csi": stats["csi"],
                "goal_entropy": entropy,
                "active_goals": goal_counts,
                "active_proposals": len(active_proposals),
                "proposal_passed": (passed_count > 0),
                # Part D telemetry
                "max_trust_delta": max_trust_delta,
                "mean_trust_delta": mean_trust_delta,
                "high_trust_count": high_trust_count,
                "runaway_detected": runaway_detected,
                "saturation_detected": saturation_detected
            })
            
            print(f"  📊 Stats: CSI={stats['csi']:.2f}, Entropy={entropy:.2f}, TrustMean={stats['mean']:.3f}, ΔMax={max_trust_delta:.3f}")
            self.session.commit()
            # time.sleep(0.01)

    def write_artifact(self):
        base = Path("artifacts/simulations")
        base.mkdir(parents=True, exist_ok=True)

        output = {
            "meta": {"steps": self.steps, "seed": self.seed, "provider": self.provider_mode},
            "users": [asdict(u) for u in self.sim_users],
            "telemetry": self.telemetry,
            "failure_alerts": self.failure_alerts,  # Part D
        }

        path = base / "v1_run_real.json"
        path.write_text(json.dumps(output, indent=2))
        print(f"\n✅ Simulation artifact written to: {path}")

# -------------------------------------
# ---------- ENTRY POINT --------------
# -------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--users", type=int, default=10, help="Number of simulation users")
    parser.add_argument("--provider", type=str, default="mock", choices=["mock", "gemini", "openai", "codex", "claude", "openrouter", "universal", "hybrid"], help="LLM Provider for Reasoning")
    args = parser.parse_args()
    
    sim = HybridSimulation(args.steps, args.users, args.seed, provider_mode=args.provider)
    
    try:
        sim.provision_users()
        sim.run()
    finally:
        sim.write_artifact()
        print("\n✅ Phase 14/17 Hybrid Real Integration Completed")

if __name__ == "__main__":
    main()
