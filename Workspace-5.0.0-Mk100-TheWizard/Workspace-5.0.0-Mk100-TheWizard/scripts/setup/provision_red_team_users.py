import asyncio
import os
import sys
from uuid import UUID
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

from jarvis.database.postgres import get_session
from jarvis.governance.models import GovernanceUser, Role

# IDs extracted from Keycloak
ADMIN1_ID = "c77f4557-376f-4512-b7ed-cc87159f9bb4"
USER1_ID = "cf87954a-70b6-498e-b770-a3cacb254ae3"
OBSERVER1_ID = "36fe9c3a-d3ef-4eb6-8d44-ccd828e2cf02"

USERS_TO_PROVISION = [
    {
        "id": ADMIN1_ID,
        "name": "admin1",
        "email": "admin1@test.com",
        "platform_role": "admin",
        "governance_role": Role.OWNER, # Mapping Genesis Logic (Role.OWNER is the config/constitutional role)
        "subject_id": f"{ADMIN1_ID}",
        "issuer": "http://keycloak:8080/realms/jarvis"
    },
    {
        "id": USER1_ID,
        "name": "user1",
        "email": "user1@test.com",
        "platform_role": "user",
        "governance_role": Role.CONTRIBUTOR, # Standard user
        "subject_id": f"{USER1_ID}",
        "issuer": "http://keycloak:8080/realms/jarvis"
    },
    {
        "id": OBSERVER1_ID,
        "name": "observer1",
        "email": "observer1@test.com",
        "platform_role": "observer",
        "governance_role": Role.OBSERVER, # Standard observer
        "subject_id": f"{OBSERVER1_ID}",
        "issuer": "http://keycloak:8080/realms/jarvis"
    }
]

def provision_users():
    print("🚀 Provisioning Test Users in Postgres...")
    with get_session() as session:
        for u_data in USERS_TO_PROVISION:
            uid = UUID(u_data["id"])
            user = session.get(GovernanceUser, uid)
            if not user:
                print(f"➕ Creating User: {u_data['name']} ({uid})")
                user = GovernanceUser(
                    id=uid,
                    name=u_data["name"],
                    # email removed - stored in Keycloak
                    platform_role=u_data["platform_role"],
                    role=u_data["governance_role"],
                    subject_id=u_data["subject_id"],
                    issuer=u_data["issuer"],
                    is_active=True
                )
                session.add(user)
            else:
                print(f"🔄 Updating User: {u_data['name']} ({uid})")
                user.platform_role = u_data["platform_role"]
                user.role = u_data["governance_role"] # Ensure correct test state
            
        session.commit()
    print("✅ Provisioning Complete.")

if __name__ == "__main__":
    provision_users()
