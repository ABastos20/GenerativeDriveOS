import sys
from jarvis.database.postgres import get_session_factory
from jarvis.governance.models import GovernanceUser, TrustScore, AuditLog, Role

def verify_genesis():
    session = get_session_factory()()
    try:
        # 1. Check Governance Users
        users = session.query(GovernanceUser).all()
        if len(users) != 1:
            print(f"❌ Verification Failed: Expected 1 user, found {len(users)}")
            sys.exit(1)
        user = users[0]
        if user.role != Role.OWNER:
            print(f"❌ Verification Failed: User role is {user.role}, expected CONSTITUTIONAL_NODE/OWNER")
            sys.exit(1)
        print(f"✅ Governance User: Verified (Subject: {user.subject_id}, Role: {user.role})")

        # 2. Check Trust Scores
        trusts = session.query(TrustScore).all()
        if len(trusts) != 1:
            print(f"❌ Verification Failed: Expected 1 trust record, found {len(trusts)}")
            sys.exit(1)
        trust = trusts[0]
        if abs(trust.reputation - 0.51) > 0.001:
             print(f"❌ Verification Failed: Trust weight is {trust.reputation}, expected 0.51")
             sys.exit(1)
        print("✅ Trust Topology:  Verified (Weight: 0.51)")

        # 3. Check Audit Log
        logs = session.query(AuditLog).all()
        if len(logs) != 1:
            print(f"❌ Verification Failed: Expected 1 audit log, found {len(logs)}")
            sys.exit(1)
        log = logs[0]
        if log.action_type != "GENESIS_BOOTSTRAP":
             print(f"❌ Verification Failed: Audit event is {log.action_type}, expected BIG_BANG/GENESIS_BOOTSTRAP")
             sys.exit(1)
        print("✅ Audit Chain:     Verified (Event: BIG_BANG)")
        
        print("\n🌟 GENESIS CEREMONY VERIFIED: The State is Valid.")

    except Exception as e:
        print(f"❌ Verification Error: {e}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    verify_genesis()
