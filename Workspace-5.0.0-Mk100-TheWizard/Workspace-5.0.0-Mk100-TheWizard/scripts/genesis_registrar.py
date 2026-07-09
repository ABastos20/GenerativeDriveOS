#!/usr/bin/env python3
"""
Genesis Registrar - bootstrap the first governance user (OWNER) exactly once.

This module mirrors scripts/setup/genesis_registrar.py but is importable as
scripts.genesis_registrar for test harnesses.
"""

import argparse
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import func

from jarvis.database.postgres import get_session_factory
from jarvis.governance.models import (
    AuditLog,
    GovernanceUser,
    PlatformRole,
    Role,
    TrustScore,
)


def genesis_bootstrap(subject_id: str, trust_weight: float, confirm: bool, issuer: str):
    """Create the constitutional owner if and only if no users exist."""
    print("🌟 [GENESIS] Initiating Sovereign Bootstrap Sequence...")
    print(f"    Target Subject: {subject_id}")
    print(f"    Issuer:         {issuer}")
    print(f"    Initial Trust:  {trust_weight}")

    SessionLocal = get_session_factory()
    session = SessionLocal()

    try:
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

        node_id = uuid.uuid4()
        genesis_user = GovernanceUser(
            id=node_id,
            name="Constitutional Anchor",
            subject_id=subject_id,
            issuer=issuer,
            role=Role.OWNER,
            platform_role=PlatformRole.ADMIN,
            is_active=True,
            trust_scores={"security": 1.0, "governance": 1.0},
        )

        trust_metric = TrustScore(
            user_id=node_id,
            epistemic_reliability=trust_weight,
            governance_consistency=trust_weight,
            historical_integrity=trust_weight,
            reputation=trust_weight,
        )

        genesis_log = AuditLog(
            action_type="GENESIS_BOOTSTRAP",
            entity_type="system",
            entity_id=node_id,
            actor_id=node_id,
            actor_type="system_root",
            old_value=None,
            new_value={"role": "OWNER", "subject": subject_id, "issuer": issuer},
            extra_data={"msg": "Universum ab initio"},
            created_at=datetime.now(timezone.utc),
        )

        session.add(genesis_user)
        session.add(trust_metric)
        session.flush()
        session.add(genesis_log)
        session.commit()

        print("✅ [GENESIS COMPLETE] The Universe has been instantiated.")
        print(f"   Node ID: {node_id}")
        print("   Status:  ACTIVE")
        print("   Role:    CONSTITUTIONAL_NODE (Owner)")

    except Exception as exc:
        session.rollback()
        print(f"❌ [CRITICAL FAILURE] Genesis aborted: {exc}")
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
