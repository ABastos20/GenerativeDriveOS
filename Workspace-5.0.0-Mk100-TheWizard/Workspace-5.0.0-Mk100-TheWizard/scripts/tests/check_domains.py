#!/usr/bin/env python3
"""Check for GD domains in Qdrant."""
from qdrant_client import QdrantClient
client = QdrantClient(host="qdrant", port=6333)

print("=== GD DOMAIN CHECK ===\n")

# Get all docs and count by domain
all_res = client.scroll(collection_name="knowledge", limit=2000, with_payload=True)
print(f"Total docs scanned: {len(all_res[0])}\n")

domain_counts = {}
for p in all_res[0]:
    d = p.payload.get("domain") if p.payload else "none"
    domain_counts[d] = domain_counts.get(d, 0) + 1

print("Domain distribution:")
for d in sorted(domain_counts.keys()):
    print(f"  {d}: {domain_counts[d]}")

# Check specifically for gd.* domains
print("\n\nGD-prefixed domains:")
for d in sorted(domain_counts.keys()):
    if d and d.startswith("gd"):
        print(f"  {d}: {domain_counts[d]}")
