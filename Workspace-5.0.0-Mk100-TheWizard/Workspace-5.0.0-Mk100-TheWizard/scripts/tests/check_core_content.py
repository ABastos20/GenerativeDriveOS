#!/usr/bin/env python3
"""Check jarvis-core chunk content."""
from qdrant_client import QdrantClient

client = QdrantClient(host="qdrant", port=6333)

print("=== JARVIS-CORE CHUNK CONTENT ===\n")

# Get jarvis-core chunks
all_res = client.scroll(collection_name="knowledge", limit=1000, with_payload=True)

for p in all_res[0]:
    pl = p.payload or {}
    domain = pl.get("domain", "")
    if domain in ("jarvis-core", "jarvis.core"):
        print(f"ID: {p.id}")
        print(f"  domain: {domain}")
        print(f"  is_system: {pl.get('is_system')}")
        print(f"  semantic_family: {pl.get('semantic_family')}")
        print(f"  source_file: {pl.get('source_file')}")
        text = pl.get("text", "")[:200]
        print(f"  text_preview: {text}...")
        print()
