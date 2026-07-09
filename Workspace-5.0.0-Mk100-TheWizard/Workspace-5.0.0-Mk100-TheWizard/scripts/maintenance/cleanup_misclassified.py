#!/usr/bin/env python3
"""Delete misclassified jarvis-core entries that contain GD content."""
from qdrant_client import QdrantClient

client = QdrantClient(host="qdrant", port=6333)
COLLECTION = "knowledge"

print("=== CLEANING MISCLASSIFIED GD ENTRIES ===\n")

# Get all docs
all_res = client.scroll(collection_name=COLLECTION, limit=5000, with_payload=True)
print(f"Total docs scanned: {len(all_res[0])}\n")

# Find jarvis-core entries that mention GD, hydrogen, water, telemetry
gd_keywords = ["gd", "generative drive", "hydrogen", "water loop", "telemetry", "gd-energy", "gd-hydrogen"]
to_delete = []

for p in all_res[0]:
    pl = p.payload or {}
    domain = pl.get("domain", "")
    source = pl.get("source_file", "")
    text = pl.get("text", "").lower()
    
    # Target jarvis-core or jarvis.core domain with GD content
    if domain in ("jarvis-core", "jarvis.core"):
        for kw in gd_keywords:
            if kw in text or kw in source.lower():
                to_delete.append(p.id)
                print(f"  Marked for deletion: id={p.id}")
                print(f"    domain={domain}")
                print(f"    source={source[:60]}")
                print(f"    matched keyword: {kw}")
                print()
                break

print(f"\nTotal to delete: {len(to_delete)}\n")

if to_delete:
    print("Deleting...")
    client.delete(
        collection_name=COLLECTION,
        points_selector=to_delete
    )
    print(f"✅ Deleted {len(to_delete)} misclassified entries")
else:
    print("No misclassified entries found to delete")

print("\n=== DONE ===")
