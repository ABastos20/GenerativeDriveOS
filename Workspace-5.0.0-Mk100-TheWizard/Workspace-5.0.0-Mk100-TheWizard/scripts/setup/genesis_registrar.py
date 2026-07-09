#!/usr/bin/env python3
"""
Genesis Registrar - The "Big Bang" of the Jarvis Governance System.

This script bootstraps the first Constitutional Node (Owner).
It enforces the "One-Time Execution" rule.
It explicitly binds a Keycloak identity (subject_id) to the foundational governance role.

Usage:
    python scripts/genesis_registrar.py --subject <uuid> --trust 0.8

Architectural Rules:
1. CAN ONLY RUN ONCE (Genesis condition: 0 users).
2. Sets Role = OWNER (Constitutional Authority).
3. Burns the key (No self-escalation possible after this).
"""
import argparse
import sys
import uuid
from datetime import datetime, timezone

# Add source path to sys.path
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import func
from jarvis.database.postgres import get_session_factory
from jarvis.governance.models import (
    GovernanceUser, 
    TrustScore, 
    AuditLog, 
    Role,
    PlatformRole,
    Permission,
    PermissionAction
)

def genesis_bootstrap(subject_id: str, trust_weight: float, confirm: bool, issuer: str):
    print(f"🌟 [GENESIS] Initiating Sovereign Bootstrap Sequence...")
    print(f"    Target Subject: {subject_id}")
    print(f"    Issuer:         {issuer}")
    print(f"    Initial Trust:  {trust_weight}")
    
    SessionLocal = get_session_factory()
    session = SessionLocal()
    
    try:
        # 1. Verify "void" state (Genesis Condition)
        user_count = session.query(func.count(GovernanceUser.id)).scalar()
        if user_count > 0:
            print(f"❌ [GENESIS FAILED] System is not empty. {user_count} users exist.")
            print("   The Big Bang can only happen once.")
            sys.exit(1)
            
        if not confirm:
            print("⚠️  [WARNING] This will permanently assign Constitutional Authority.")
            res = input("   Are you sure? (type 'YES' to proceed): ")
            if res.strip() != "YES":
                print("ABORTED.")
                sys.exit(0)

        # 2. Create the Constitutional Node
        node_id = uuid.uuid4()
        
        # We explicitly map "Constitutional Node" to Role.OWNER permissions
        genesis_user = GovernanceUser(
            id=node_id,
            name="Constitutional Anchor",
            subject_id=subject_id,
            issuer=issuer, 
            role=Role.OWNER,
            platform_role=PlatformRole.ADMIN,
            is_active=True,
            trust_scores={"security": 1.0, "governance": 1.0}
        )
        
        # 3. Assign Trust Weight
        trust_metric = TrustScore(
            user_id=node_id,
            epistemic_reliability=trust_weight,
            governance_consistency=trust_weight,
            historical_integrity=trust_weight,
            reputation=trust_weight
        )
        
        # 4. Create Audit Trail (The First Log)
        genesis_log = AuditLog(
            action_type="GENESIS_BOOTSTRAP",
            entity_type="system",
            entity_id=node_id,
            actor_id=node_id, # Self-signed by the anchor
            actor_type="system_root",
            old_value=None,
            new_value={"role": "OWNER", "subject": subject_id, "issuer": issuer},
            extra_data={"msg": "Universum ab initio"}
        )
        
        session.add(genesis_user)
        session.add(trust_metric)
        session.flush() # Ensure user exists for actor_id FK
        
        session.add(genesis_log)
        
        session.commit()
        
        print("✅ [GENESIS COMPLETE] The Universe has been instantiated.")
        print(f"   Node ID: {node_id}")
        print("   Status:  ACTIVE")
        print("   Role:    CONSTITUTIONAL_NODE (Owner)")
        
    except Exception as e:
        session.rollback()
        print(f"❌ [CRITICAL FAILURE] Genesis aborted: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jarvis Genesis Registrar")
    parser.add_argument("--subject", required=True, help="Keycloak Subject UUID")
    parser.add_argument("--trust", type=float, default=0.51, help="Initial Trust Weight (0.0-1.0)")
    parser.add_argument("--issuer", default="https://jarvis.sovereign.idp", help="OIDC Issuer URL")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    
    args = parser.parse_args()
    
    genesis_bootstrap(args.subject, args.trust, args.yes, args.issuer)
