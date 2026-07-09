#!/usr/bin/env python3
"""Diagnostic script per architect notes."""
from qdrant_client import QdrantClient
client = QdrantClient(host="qdrant", port=6333)

print("=== GD DOCS DIAGNOSTIC ===\n")

# 1. Check GD domain docs
print("1. Checking for 'gd' domain...")
res = client.scroll(
    collection_name="knowledge",
    scroll_filter={"must": [
        {"key": "domain", "match": {"value": "gd"}}
    ]},
    limit=200
)
print(f"   Found: {len(res[0])} docs with domain='gd'\n")

# 2. Check all unique domains
print("2. All unique domains in collection:")
all_res = client.scroll(collection_name="knowledge", limit=500, with_payload=True)
domains = set()
for p in all_res[0]:
    d = p.payload.get("domain") if p.payload else None
    if d:
        domains.add(d)
for d in sorted(domains):
    print(f"   - {d}")

# 3. Check docs containing "hydrogen" or "water" in text
print("\n3. Docs mentioning 'hydrogen' or 'water':")
for p in all_res[0]:
    text = p.payload.get("text", "") if p.payload else ""
    if "hydrogen" in text.lower() or "water" in text.lower():
        domain = p.payload.get("domain") if p.payload else "?"
        sf = p.payload.get("semantic_family") if p.payload else "?"
        print(f"   domain={domain} sf={sf} text_preview={text[:80]}...")

print("\n4. Check RetrievalMode for GD query:")
from jarvis.memory.search import detect_retrieval_mode
mode, date = detect_retrieval_mode("Explain the hydrogen water loop concept in GD")
print(f"   Detected mode: {mode.value}")
print(f"   Detected date: {date}")

print("\n=== DONE ===")
