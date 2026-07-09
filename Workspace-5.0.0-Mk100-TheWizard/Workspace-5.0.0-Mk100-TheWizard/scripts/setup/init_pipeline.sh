#!/bin/bash
# JARVIS Pipeline Initialization Script
#
# This script initializes the full JARVIS pipeline:
# 1. Verifies environment variables
# 2. Initializes Qdrant collection
# 3. Ensures Postgres tables exist
# 4. Sets up cron jobs for background tasks
# 5. Verifies CLI tool availability

set -e

echo "=========================================="
echo "JARVIS Pipeline Initialization"
echo "=========================================="
echo ""

# 1. Check Environment
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "WARNING: GOOGLE_API_KEY is not set. LLM features may fail."
fi

# 2. Initialize Database & Qdrant
echo "Initializing Databases..."
# We run a python snippet to ensure tables and collections exist
docker exec jarvis-app python -c "
from jarvis.database.models import Base
from jarvis.database.postgres import get_engine
from jarvis.database.qdrant import init_collection
import structlog

logger = structlog.get_logger()

print('Creating Postgres tables...')
try:
    Base.metadata.create_all(get_engine())
    print('✓ Postgres tables created/verified')
except Exception as e:
    print(f'✗ Postgres init failed: {e}')

print('Initializing Qdrant collection...')
try:
    # We use the default collection name from config
    if init_collection():
        print('✓ Qdrant collection initialized')
except Exception as e:
    print(f'✗ Qdrant init failed: {e}')
"

# 3. Setup Cron Jobs
echo "Setting up Cron Jobs..."
# Run the setup-cron.sh script inside the container
# Ensure script is executable
docker exec jarvis-app chmod +x /workspace/scripts/setup-cron.sh
docker exec jarvis-app /workspace/scripts/setup-cron.sh

# 4. Verify CLI Tools
echo "Verifying CLI Tools..."
docker exec jarvis-app python -c "
import shutil
tools = ['git', 'grep', 'curl']
missing = [t for t in tools if not shutil.which(t)]
if missing:
    print(f'WARNING: Missing CLI tools: {missing}')
else:
    print('✓ Basic CLI tools verified.')
"

echo ""
echo "=========================================="
echo "Pipeline Initialized Successfully!"
echo "=========================================="
