#!/usr/bin/env python3
"""Test script to verify Vision Mode filtering."""
import sys
OUTPUT_FILE = "/tmp/vision_mode_test.txt"
sys.stdout = open(OUTPUT_FILE, "w")

from jarvis.memory.search import search_memory, RetrievalMode, _build_filter_for_mode
from qdrant_client import models as qmodels

print("=== TESTING VISION MODE FILTER ===\n")

# 1. Test filter construction
print("1. Testing _build_filter_for_mode...")
flt = _build_filter_for_mode(
    mode=RetrievalMode.NORMAL,
    include_system_docs=False,
    allow_stale=False,
)

print(f"   Filter: {flt}")
print(f"   must_not conditions: {len(flt.must_not) if flt.must_not else 0}")
for cond in (flt.must_not or []):
    print(f"     - {cond}")
print()

# 2. Test search_memory with NORMAL mode
print("2. Testing search_memory with NORMAL mode...")
try:
    results = search_memory(
        "Explain hydrogen water loop",
        k=10,
        retrieval_mode=RetrievalMode.NORMAL,
    )
    
    print(f"   Got {len(results)} results")
    is_system_count = 0
    for r in results[:10]:
        meta = r.metadata or {}
        is_sys = meta.get("is_system")
        if is_sys:
            is_system_count += 1
        print(f"   - is_system={is_sys} domain={r.domain} sf={meta.get('semantic_family')}")
    
    if is_system_count > 0:
        print(f"\n   ❌ LEAK: {is_system_count} system docs in NORMAL mode!")
    else:
        print(f"\n   ✅ No system doc leak")
except Exception as e:
    print(f"   Error: {e}")

print()

# 3. Test META mode (should include system)
print("3. Testing search_memory with META mode...")
try:
    results = search_memory(
        "Summarise memory.core.md",
        k=10,
        retrieval_mode=RetrievalMode.META,
    )
    
    print(f"   Got {len(results)} results")
    is_system_count = 0
    for r in results[:5]:
        meta = r.metadata or {}
        is_sys = meta.get("is_system")
        if is_sys:
            is_system_count += 1
        print(f"   - is_system={is_sys} domain={r.domain} sf={meta.get('semantic_family')}")
    
    if is_system_count > 0:
        print(f"\n   ✅ META mode includes {is_system_count} system docs (expected)")
    else:
        print(f"\n   ⚠️  No system docs found in META mode")
except Exception as e:
    print(f"   Error: {e}")

print()

# 4. Check if jarvis-core domain correlates with is_system
print("4. Checking jarvis-core domain correlation...")
from qdrant_client import QdrantClient
c = QdrantClient(host="qdrant", port=6333)
r = c.scroll(collection_name="knowledge", limit=200, with_payload=True)
jc_count = 0
jc_is_sys = 0
for p in r[0]:
    pl = p.payload or {}
    if pl.get("domain") == "jarvis-core":
        jc_count += 1
        if pl.get("is_system"):
            jc_is_sys += 1
print(f"   domain='jarvis-core': {jc_count}")
print(f"   of those, is_system=True: {jc_is_sys}")

# 5. Check what domains are on the is_system=True docs
print()
print("5. Domains of is_system=True documents:")
for p in r[0]:
    pl = p.payload or {}
    if pl.get("is_system"):
        print(f"   domain={pl.get('domain')} sf={pl.get('semantic_family')}")

print("\n=== DONE ===")
