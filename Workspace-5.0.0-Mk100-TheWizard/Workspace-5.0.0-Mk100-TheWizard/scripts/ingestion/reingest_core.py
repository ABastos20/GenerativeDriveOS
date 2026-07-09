#!/usr/bin/env python3
"""Re-ingest jarvis-core docs properly with is_system=True."""
from pathlib import Path
from jarvis.memory.ingest import ingest_file

CORE_FILES = [
    (Path("/workspace/docs/jarvis/memory.core.md"), "jarvis.core"),
]

print("=== RE-INGESTING JARVIS-CORE DOCS ===\n")

for filepath, domain in CORE_FILES:
    print(f"Ingesting: {filepath}")
    print(f"  Domain: {domain}")
    try:
        result = ingest_file(
            filepath,
            domain=domain,
            meta={
                "is_system": True,  # System plane
                "semantic_family": "core-memory",
                "priority": 0.9,  # High priority for META mode
            }
        )
        print(f"  ✅ Ingested successfully: {result}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()

print("=== DONE ===")
