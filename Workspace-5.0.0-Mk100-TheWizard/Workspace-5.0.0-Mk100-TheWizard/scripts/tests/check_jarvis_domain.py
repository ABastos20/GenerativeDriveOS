#!/usr/bin/env python3
"""Check correlation between domain and is_system."""
from qdrant_client import QdrantClient
c = QdrantClient(host="qdrant", port=6333)
r = c.scroll(collection_name="knowledge", limit=500, with_payload=True)

# Count domain=jarvis.core with and without is_system
jc_with_sys = 0
jc_without_sys = 0
for p in r[0]:
    pl = p.payload or {}
    domain = pl.get("domain") or ""
    if "jarvis" in domain.lower():
        if pl.get("is_system"):
            jc_with_sys += 1
        else:
            jc_without_sys += 1
        print(f"domain={domain} is_system={pl.get('is_system')} sf={pl.get('semantic_family')}")

print()
print(f"SUMMARY: jarvis domains with is_system=True: {jc_with_sys}")
print(f"SUMMARY: jarvis domains with is_system=False/None: {jc_without_sys}")
