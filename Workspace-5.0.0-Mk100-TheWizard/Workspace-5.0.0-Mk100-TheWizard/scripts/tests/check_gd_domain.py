#!/usr/bin/env python3
"""Check GD playbook domain."""
from qdrant_client import QdrantClient
client = QdrantClient(host="qdrant", port=6333)

print("=== GD PLAYBOOK CHECK ===\n")

# Check all docs, find ones with "GD" in source_file or text
all_res = client.scroll(collection_name="knowledge", limit=1000, with_payload=True)
print(f"Total docs: {len(all_res[0])}\n")

gd_docs = []
for p in all_res[0]:
    pl = p.payload or {}
    source = pl.get("source_file", "") or ""
    text = pl.get("text", "") or ""
    if "gd" in source.lower() or "generative drive" in text.lower() or "GD" in text:
        gd_docs.append(pl)
        
print(f"Docs matching GD criteria: {len(gd_docs)}\n")
for doc in gd_docs[:10]:
    print(f"domain={doc.get('domain')}")
    print(f"is_system={doc.get('is_system')}")
    print(f"semantic_family={doc.get('semantic_family')}")
    print(f"source={doc.get('source_file', '')[:60]}")
    print(f"text_preview={doc.get('text', '')[:100]}...")
    print()
