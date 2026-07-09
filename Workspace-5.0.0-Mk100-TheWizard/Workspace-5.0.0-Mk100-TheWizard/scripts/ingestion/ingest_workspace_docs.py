#!/usr/bin/env python3
"""
Ingest all workspace documentation into Qdrant using CORE classification policies.
Logic has been moved to src/jarvis/memory/domain_classifiers.py and src/jarvis/memory/ingest.py.
"""
import sys
from pathlib import Path

# Add src to path
WORKSPACE_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(WORKSPACE_ROOT / "src"))

import structlog
from jarvis.memory.ingest import ingest_file

logger = structlog.get_logger()

WORKSPACE_DOCS = WORKSPACE_ROOT / "docs"

def main():
    if not WORKSPACE_DOCS.exists():
        print(f"Docs dir not found: {WORKSPACE_DOCS}")
        return

    print("════════════════════════════════════════════════════════════")
    print("📚 JARVIS KNOWLEDGE INGESTION (Core Policy)")
    print("   Logic transported to src/jarvis/memory/domain_classifiers.py")
    print("════════════════════════════════════════════════════════════")

    count = 0
    # Walk docs directory
    all_files = list(WORKSPACE_DOCS.rglob("*"))
    
    # Filter for ingestible files
    doc_files = [
        f for f in all_files 
        if f.is_file() and f.suffix.lower() in {".md", ".markdown", ".txt", ".pdf"}
    ]
    
    # Sort for deterministic order (optional)
    doc_files.sort()
    
    print(f"\nFound {len(doc_files)} documents\n")

    for path in doc_files:
        try:
            # We call ingest_file without arguments, letting the core policy discover:
            # - domain
            # - tags
            # - metadata (is_system, etc.)
            ingest_file(path)
            count += 1
            if count % 10 == 0:
                print(f"Processed {count} files...")
        except Exception as e:
            logger.error("ingest_failed", path=str(path), error=str(e))

    print(f"\n✅ Ingestion complete. Processed {count} documents.")

if __name__ == "__main__":
    main()
