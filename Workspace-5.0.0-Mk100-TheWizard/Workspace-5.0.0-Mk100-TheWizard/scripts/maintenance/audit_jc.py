#!/usr/bin/env python3
"""Full purge of jarvis-core that shouldn't exist, then verify GD."""
from qdrant_client import QdrantClient

client = QdrantClient(host="qdrant", port=6333)
COLLECTION = "knowledge"

print("=== FULL JARVIS-CORE AUDIT ===\n")

# Get all docs
all_res = client.scroll(collection_name=COLLECTION, limit=5000, with_payload=True)
print(f"Total docs: {len(all_res[0])}\n")

# Count jarvis-core and jarvis.core
jc_count = 0
jc_ids = []
for p in all_res[0]:
    pl = p.payload or {}
    domain = pl.get("domain", "")
    if domain in ("jarvis-core", "jarvis.core"):
        jc_count += 1
        jc_ids.append(p.id)
        is_sys = pl.get("is_system")
        sf = pl.get("semantic_family")
        src = pl.get("source_file", "")[:60]
        print(f"  id={p.id} is_system={is_sys} sf={sf}")
        print(f"    source={src}")

print(f"\nTotal jarvis-core/jarvis.core entries: {jc_count}")

# Check if any have is_system=False (shouldn't be in jarvis-core anyway)
non_system_jc = [p for p in all_res[0] 
                 if p.payload and p.payload.get("domain") in ("jarvis-core", "jarvis.core")
                 and not p.payload.get("is_system")]
print(f"Of those, is_system=False/None: {len(non_system_jc)}")

# Show GD domains
print("\n\nGD-prefixed domains remaining:")
gd_count = 0
for p in all_res[0]:
    d = p.payload.get("domain", "") if p.payload else ""
    if d.startswith("gd"):
        gd_count += 1
print(f"  Total gd.* docs: {gd_count}")
