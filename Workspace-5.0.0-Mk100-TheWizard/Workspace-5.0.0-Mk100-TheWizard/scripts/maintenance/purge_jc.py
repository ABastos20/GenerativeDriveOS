#!/usr/bin/env python3
"""Delete ALL jarvis-core/jarvis.core entries for clean experiment."""
from qdrant_client import QdrantClient

client = QdrantClient(host="qdrant", port=6333)
COLLECTION = "knowledge"

print("=== PURGING ALL JARVIS-CORE ENTRIES ===\n")

# Get all docs
all_res = client.scroll(collection_name=COLLECTION, limit=5000, with_payload=True)

# Collect all jarvis-core and jarvis.core IDs
jc_ids = []
for p in all_res[0]:
    pl = p.payload or {}
    domain = pl.get("domain", "")
    if domain in ("jarvis-core", "jarvis.core"):
        jc_ids.append(p.id)

print(f"Found {len(jc_ids)} jarvis-core/jarvis.core entries")

if jc_ids:
    print("Deleting ALL of them...")
    client.delete(
        collection_name=COLLECTION,
        points_selector=jc_ids
    )
    print(f"✅ Deleted {len(jc_ids)} entries")

print("\n=== DONE ===")
