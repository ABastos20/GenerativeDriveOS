import sys
import os
import structlog
from dotenv import load_dotenv

load_dotenv()

# Force localhost for manual script
os.environ["POSTGRES_HOST"] = "localhost"

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.getcwd())

from jarvis.database.postgres import get_session_factory
from jarvis.governance.models import GovernanceUser, TrustScore, AuditLog, Escalation, Proposal, Vote
from jarvis.database.models import Message, Conversation, ResearchLog
from scripts.genesis_registrar import genesis_bootstrap
from sqlalchemy import text

def nuke():
    print("WARNING: NUKING DATABASE...")
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        # Cascade delete is safer with ORM or direct SQL
        # Using raw SQL for speed and ensuring everything goes
        tables = [
            "votes", "proposals", "escalations", 
            "trust_scores", "governance_audit_log", "governance_users"
            # Note: keeping chat history for now as User might value it? 
            # "Nuke & Genesis" usually refers to Governance State.
            # But "Persona" verification might need clean chat state? 
            # I'll leave chat history intact unless strict instruction.
            # User said "Nuke & Genesis verification". 
            # Let's clean ONLY Governance.
        ]
        
        for t in tables:
            print(f"  Dropping {t}...")
            session.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
            
        session.commit()
        print("DATABASE NUKED (Governance Only).")
    except Exception as e:
        print(f"Error nuking: {e}")
        session.rollback()
    finally:
        session.close()

def run_genesis():
    # Use a dummy subject ID (or the User's if known? No, use dummy for test)
    # The architect said: "Verify Persona behavior... Perform the 'Nuke & Genesis' verification"
    # This might mean "Run the Genesis script".
    subject = "genesis-verifier-subject-001"
    print(f"Running Genesis for Subject: {subject}")
    genesis_bootstrap(subject, 1.0, confirm=True, issuer="verification")

if __name__ == "__main__":
    nuke()
    run_genesis()
