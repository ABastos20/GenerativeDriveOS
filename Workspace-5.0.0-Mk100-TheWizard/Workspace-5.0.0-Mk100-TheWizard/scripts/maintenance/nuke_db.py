import sys
import logging
from sqlalchemy import text
from jarvis.database.postgres import get_session_factory

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def nuke_database():
    """Drop all tables and types to simulate a fresh install."""
    
    confirm = input("⚠️ CRITICAL WARNING: This will DELETE ALL DATA in the database. Type 'NUKE' to proceed: ")
    if confirm != "NUKE":
        print("Aborted.")
        sys.exit(0)
        
    session_factory = get_session_factory()
    session = session_factory()
    
    logger.info("☢️ Initiating Nuclear Launch Sequence...")
    
    try:
        # Disable constraints to allow dropping in any order
        session.execute(text("SET session_replication_role = 'replica';"))
        
        # Drop all tables in public schema
        session.execute(text("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        
        # Drop custom types (enums)
        session.execute(text("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT typname FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid WHERE n.nspname = 'public' AND t.typtype = 'e') LOOP
                    EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        
        # Drop alembic version table explicitly if missed
        session.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
        
        # Re-enable constraints
        session.execute(text("SET session_replication_role = 'origin';"))
        
        session.commit()
        logger.info("✅ TANGO DOWN. Database is effectively empty.")
        
    except Exception as e:
        logger.error(f"❌ Nuke failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    nuke_database()
