
import os
import sys
from uuid import UUID, uuid4
from datetime import datetime, timezone

# Add workspace root to path
sys.path.append(os.getcwd())

from jarvis.database.postgres import get_session
from jarvis.governance.models import (
    GovernanceUser, 
    Role, 
    TrustScore, 
    Constitution,
    Permission
)

DEFAULT_USERS = [
    {"id": "00000000-0000-0000-0000-000000000001", "name": "Admin_1", "role": Role.OWNER, "subject_id": "mock:admin1", "issuer": "https://jarvis.sovereign.idp"},
    {"id": "00000000-0000-0000-0000-000000000002", "name": "Contributor_1", "role": Role.CONTRIBUTOR, "subject_id": "mock:contrib1", "issuer": "https://jarvis.sovereign.idp"},
    {"id": "00000000-0000-0000-0000-000000000003", "name": "Observer_1", "role": Role.OBSERVER, "subject_id": "mock:observer1", "issuer": "https://jarvis.sovereign.idp"},
]

def bootstrap():
    print("Bootstrapping Governance System...")
    
    with get_session() as session:
        # 1. Ensure Constitution
        const = session.query(Constitution).filter_by(active=True).first()
        if not const:
            print("Creating default Constitution...")
            const = Constitution(active=True)
            session.add(const)
        
        # 2. Bootstrap Users
        for u_data in DEFAULT_USERS:
            uid = UUID(u_data["id"])
            user = session.get(GovernanceUser, uid)
            if not user:
                print(f"Creating user: {u_data['name']}")
                user = GovernanceUser(
                    id=uid,
                    name=u_data["name"],
                    role=u_data["role"],
                    subject_id=u_data["subject_id"],
                    issuer=u_data["issuer"],
                    is_active=True
                )
                session.add(user)
                session.flush() # Get ID if needed, but we set it manually
            else:
                print(f"User exists: {u_data['name']}")
                
            # 3. Bootstrap Trust Scores (User Req #2)
            if not user.trust_metrics:
                print(f"  -> Initializing Trust Score for {user.name}")
                ts = TrustScore(
                    user_id=user.id,
                    epistemic_reliability=0.8 if user.role == Role.OWNER else 0.5,
                    governance_consistency=0.9 if user.role == Role.OWNER else 0.5,
                    historical_integrity=1.0,
                    reputation=0.7
                )
                session.add(ts)
                
        session.commit()
        print("Bootstrap complete. Trust scores initialized.")

if __name__ == "__main__":
    bootstrap()
