
import sys
import os
import random
from uuid import uuid4
from datetime import datetime, timezone

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from jarvis.database.postgres import get_connection_string, get_engine
from jarvis.governance.models import (
    GovernanceUser, Role, TrustScore, Proposal, ProposalStatus, 
    ProposalType, Vote, VoteChoice, Constitution
)
from jarvis.governance.voting import ProposalManager, VotingEngine
from jarvis.governance.constitution import ConstitutionalGuard
from jarvis.governance.trust import TrustCalculator

# Setup DB
# engine = create_engine(get_db_url())
# SessionLocal = sessionmaker(bind=engine)
engine = get_engine()
SessionLocal = sessionmaker(bind=engine)

def banner(msg):
    print(f"\n{'='*60}")
    print(f" {msg}")
    print(f"{'='*60}")

def simulate():
    session = SessionLocal()
    
    try:
        banner("SIMULATION START: v1 Governance Kernel Freeze")
        
        # 1. Ensure Constitution
        banner("1. Bootstrapping Constitution")
        constitution = ConstitutionalGuard.get_active_constitution(session)
        print(f"Active Constitution ID: {constitution.id}")
        print(f"Params: Sybil={constitution.sybil_threshold}, Floor={constitution.minority_floor}, Cap={constitution.anti_elite_multiplier}x")

        # 2. Create Users (3 Tiers)
        banner("2. Creating User Population (10 Users)")
        
        tiers = [
            ("High", 3, 0.95),  # Elders
            ("Mid", 4, 0.60),   # Citizens
            ("Low", 3, 0.10)    # New/Sybil
        ]
        
        sim_users = []
        
        for tier_name, count, trust_val in tiers:
            for i in range(count):
                u_id = uuid4()
                email = f"sim_{tier_name.lower()}_{i}_{str(u_id)[:4]}@simulation.local"
                
                # Check if exists (cleanup from prev run?)
                # user = session.query(GovernanceUser).filter_by(email=email).first()
                # If we want fresh run every time, maybe use unique emails
                
                user = GovernanceUser(
                    id=u_id,
                    email=email,
                    name=f"{tier_name}_User_{i}",
                    role=Role.CONTRIBUTOR if tier_name != "High" else Role.ADMIN,
                    is_active=True
                )
                
                # Trust Score
                ts = TrustScore(
                    user_id=u_id,
                    epistemic_reliability=trust_val,
                    governance_consistency=trust_val,
                    historical_integrity=trust_val,
                    reputation=trust_val
                )
                user.trust_metrics = ts
                
                session.add(user)
                sim_users.append({'user': user, 'tier': tier_name})
                
        session.commit()
        
        # Calculate Initial System Weight
        v_engine = VotingEngine(session)
        snapshot, total_sys_weight = v_engine.create_trust_snapshot()
        
        print(f"Users Created: {len(sim_users)}")
        print(f"Total System Weight: {total_sys_weight:.4f}")
        
        # Show Weight Distribution
        print("\n--- Weight Distribution ---")
        for u_data in sim_users:
            u = u_data['user']
            weight = v_engine._compute_vote_weight(u, constitution)
            print(f"[{u_data['tier']}] {u.name}: Trust={u.trust_metrics.epistemic_reliability:.2f} -> Weight={weight:.4f}")

        # 3. Conflict Scenarios
        banner("3. Running Conflict Scenarios")
        
        scenarios = [
            ("Unanimous Consent", "High:FOR, Mid:FOR, Low:FOR", True),
            ("The Reject", "High:AGAINST, Mid:AGAINST, Low:AGAINST", False),
            ("Class War (Elites vs Masses)", "High:FOR, Mid:AGAINST, Low:AGAINST", None), 
            ("The Sybil Attack", "High:AGAINST, Mid:ABSTAIN, Low:FOR", None),
            ("Close Call", "Random", None)
        ]
        
        p_mgr = ProposalManager(session)
        proposer = sim_users[0]['user'] # Elite proposer
        
        for idx, (scn_name, pattern, expected_pass) in enumerate(scenarios):
            print(f"\nScenario {idx+1}: {scn_name}")
            print(f"Pattern: {pattern}")
            
            # Create
            prop = p_mgr.create_proposal(
                title=f"Sim Prop {idx+1}: {scn_name}",
                description=f"Simulation of {pattern}",
                proposer=proposer,
                duration_hours=24
            )
            session.commit()
            
            # Open
            p_mgr.open_proposal(prop.id, proposer)
            session.commit()
            
            # Vote
            for u_data in sim_users:
                u = u_data['user']
                tier = u_data['tier']
                choice = VoteChoice.ABSTAIN
                
                if pattern == "Random":
                    choice = random.choice(list(VoteChoice))
                elif "High:FOR" in pattern and tier == "High": choice = VoteChoice.FOR
                elif "High:AGAINST" in pattern and tier == "High": choice = VoteChoice.AGAINST
                elif "Mid:FOR" in pattern and tier == "Mid": choice = VoteChoice.FOR
                elif "Mid:AGAINST" in pattern and tier == "Mid": choice = VoteChoice.AGAINST
                elif "Low:FOR" in pattern and tier == "Low": choice = VoteChoice.FOR
                elif "Low:AGAINST" in pattern and tier == "Low": choice = VoteChoice.AGAINST
                
                try:
                    v_engine.cast_vote(prop.id, u, choice)
                except Exception as e:
                    print(f"Vote Failed for {u.name}: {e}")
            
            session.commit()
            
            # Tally
            results = v_engine.tally_votes(prop.id)
            print(f"Results: {results['current_approval']:.1%} Approval (Threshold {results['approval_threshold']:.1%})")
            print(f"Quorum: {results['current_quorum']:.1%} (Required {results['quorum_required']:.1%})")
            print(f"Votes: For={results['total_for']:.2f}, Against={results['total_against']:.2f}")
            
            # Resolve
            # Force deadline pass manually? Or cheat the clock?
            # VotingEngine.resolve_proposal checks deadline. We must override or mock time.
            # For sim, we can force status if logic permits, or we mock datetime.
            # Let's direct update deadline to past.
            prop.deadline = datetime.now(timezone.utc)
            session.commit()
            
            try:
                final_prop = v_engine.resolve_proposal(prop.id)
                print(f"FINAL STATUS: {final_prop.status.value}")
                print(f"Reason: {final_prop.resolution_reason}")
            except Exception as e:
                print(f"Resolution Failed: {e}")
                
        # 4. Constitutional Amendment
        banner("4. Constitutional Amendment Attempt")
        
        # Grant Owner role to proposer to allow AMEND action
        proposer.role = Role.OWNER
        session.commit()
        print(f"Upgraded {proposer.name} to OWNER to propose amendment.")
        
        amend_prop = p_mgr.create_proposal(
            title="Sim: Reduce Sybil Threshold",
            description="Trying to lower the bar to 0.0",
            proposer=proposer,
            proposal_type=ProposalType.CONSTITUTIONAL_AMENDMENT
        )
        session.commit()
        p_mgr.open_proposal(amend_prop.id, proposer)
        session.commit()
        
        print("Attempting to pass with ONLY High Tier (3 users)...")
        for u_data in sim_users:
            if u_data['tier'] == "High":
                v_engine.cast_vote(amend_prop.id, u_data['user'], VoteChoice.FOR)
        
        session.commit()
        
        # Check Quorum
        amend_res = v_engine.tally_votes(amend_prop.id)
        print(f"Current Quorum: {amend_res['current_quorum']:.1%} (Need 75%)")
        
        # Add Mid Tier to pass Quorum
        print("Adding Mid Tier votes...")
        for u_data in sim_users:
            if u_data['tier'] == "Mid":
                v_engine.cast_vote(amend_prop.id, u_data['user'], VoteChoice.FOR)
        session.commit()
        
        amend_res = v_engine.tally_votes(amend_prop.id)
        print(f"New Quorum: {amend_res['current_quorum']:.1%}")
        print(f"Approval: {amend_res['current_approval']:.1%} (Need 80%)")
        
        # Resolve
        amend_prop.deadline = datetime.now(timezone.utc)
        final_amend = v_engine.resolve_proposal(amend_prop.id)
        print(f"AMENDMENT STATUS: {final_amend.status.value}")

        banner("SIMULATION COMPLETE")
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    simulate()
