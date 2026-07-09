import sys
import logging
from jarvis.database.postgres import get_engine
from jarvis.database.models import Base
# Import all model modules side-effects
import jarvis.database.models
import jarvis.governance.models 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_schema():
    engine = get_engine()
    logger.info("🔧 Forcing schema creation from models...")
    try:
        Base.metadata.create_all(engine)
        logger.info("✅ Schema created successfully.")
    except Exception as e:
        logger.error(f"❌ Schema creation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    force_schema()
