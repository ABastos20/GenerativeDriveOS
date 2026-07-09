"""Unsafe full reset and re-ingestion script for JARVIS.

Wipes 'jarvis-memory' collection in Qdrant and re-ingests everything in docs/,
STRICTLY EXCLUDING data/docs/gptExportNew.
"""
import os
import sys
from pathlib import Path

# Ensure src/ is in path
sys.path.append(str(Path("/app/src")))

from jarvis.database.qdrant import get_qdrant_client, DEFAULT_COLLECTION_NAME
from jarvis.memory.ingest import ingest_file
from jarvis.database.models import Base
from jarvis.database.postgres import get_engine
import subprocess

def main():
    print("🛑 STARTING FULL SYSTEM RESET (POSTGRES + MEMORY) 🛑")
    
    # 1. Wipe Postgres
    print("🗑️  Wiping PostgreSQL Database...")
    try:
        engine = get_engine()
        # Dispose engine to close connections
        engine.dispose()
        
        Base.metadata.drop_all(bind=engine)
        print("   ✅ Tables dropped.")
        
        Base.metadata.create_all(bind=engine)
        print("   ✅ Tables recreated.")
        
        try:
            # Stamp alembic so proper migrations work in future
            print("   ⏳ Stamping alembic head...")
            subprocess.run(["alembic", "stamp", "head"], check=True, capture_output=True)
            print("   ✅ Alembic stamped to head.")
        except Exception as e:
             # Just a warning, system works without alembic stamp usually if models match
            print(f"   ⚠️  Alembic stamp skipped: {e}")

    except Exception as e:
        print(f"❌ Postgres wipe failed: {e}")
        # Continue? Yes, try to wipe memory at least.

    # 2. Wipe Qdrant
    print(f"🗑️  Wiping Qdrant Collection '{DEFAULT_COLLECTION_NAME}'...")
    client = get_qdrant_client()
    try:
        client.delete_collection(DEFAULT_COLLECTION_NAME)
        print("✅ Collection deleted.")
    except Exception as e:
        print(f"⚠️  Delete failed (maybe didn't exist): {e}")

    # 2. Ingest Docs
    # Try container path first, then local (for testing)
    docs_root = Path("/app/docs")
    if not docs_root.exists():
        docs_root = Path("docs").resolve()
        
    if not docs_root.exists():
        print(f"❌ Docs directory not found at {docs_root}")
        sys.exit(1)

    print(f"📂 Ingesting from: {docs_root}")
    
    excludes = {"gptExportNEW", "gptExportNew", ".git", "__pycache__"}
    
    success_count = 0
    skipped_count = 0
    
    for root, dirs, files in os.walk(docs_root):
        # Filter directories inplace to prevent traversing them
        # Use simple string matching for safety
        dirs[:] = [d for d in dirs if d not in excludes and "gptExport" not in d]
        
        for file in files:
            file_path = Path(root) / file
            
            # Double check path for safety
            if "gptExport" in str(file_path):
                print(f"🛡️  SKIPPING UNSAFE FILE: {file_path}")
                skipped_count += 1
                continue
                
            if file_path.suffix.lower() in {".md", ".txt", ".pdf", ".docx", ".json"}:
                try:
                    # print(f"📄 Ingesting: {file_path.name}")
                    ingest_file(file_path, collection_name=DEFAULT_COLLECTION_NAME)
                    success_count += 1
                    if success_count % 10 == 0:
                        print(f"   ... ingested {success_count} files")
                except Exception as e:
                    print(f"❌ Error ingesting {file_path.name}: {e}")

    print(f"\n✅ DONE. Ingested {success_count} files. Skipped {skipped_count} unsafe/other files.")

if __name__ == "__main__":
    main()
