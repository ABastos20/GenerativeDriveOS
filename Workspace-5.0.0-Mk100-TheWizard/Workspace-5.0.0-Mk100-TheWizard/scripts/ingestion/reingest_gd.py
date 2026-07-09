#!/usr/bin/env python3
"""Re-ingest GD docs with correct domain classification."""
from pathlib import Path
from jarvis.memory.ingest import ingest_file

GD_FILES = [
    (Path("/workspace/docs/jarvis/playbooks/gd-energy-partnerships.md"), "gd.partnerships"),
    (Path("/workspace/docs/jarvis/playbooks/gd-hydrogen-and-water-loop.md"), "gd.hydrogen"),
    (Path("/workspace/docs/jarvis/playbooks/gd-telemetry-and-infra.md"), "gd.telemetry"),
    (Path("/workspace/docs/jarvis/gd-overview.md"), "gd"),
]

print("=== RE-INGESTING GD DOCS ===\n")

for filepath, domain in GD_FILES:
    print(f"Ingesting: {filepath}")
    print(f"  Domain: {domain}")
    try:
        result = ingest_file(
            filepath,
            domain=domain,
            meta={
                "is_system": False,
                "semantic_family": "gd-playbook",
            }
        )
        print(f"  ✅ Ingested successfully: {result}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()

print("=== DONE ===")
