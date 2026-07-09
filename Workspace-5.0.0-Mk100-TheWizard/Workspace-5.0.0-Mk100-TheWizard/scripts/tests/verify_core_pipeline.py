#!/usr/bin/env python3
"""Full pipeline trace for core retrieval balance."""
import sys
sys.path.insert(0, "/workspace/src")

# Redirect output to file
out = open("/tmp/pipeline_trace.txt", "w")
def p(s=""): 
    print(s)
    out.write(s + "\n")
    out.flush()

from jarvis.memory.search import (
    search_memory, 
    detect_retrieval_mode, 
    infer_query_domains,
    RetrievalMode
)

print("=== CORE PIPELINE VERIFICATION ===\n")

# Test queries
QUERIES = [
    ("Explain the hydrogen water loop in GD", "Should be NORMAL, GD wins"),
    ("Summarize memory.core.md", "Should be META, core wins"),
    ("What are Ariel's core memory instructions?", "Should be META, core wins"),
    ("How does Jarvis memory system work?", "Should be META, core wins"),
]

for query, expected in QUERIES:
    print(f"Query: {query}")
    print(f"Expected: {expected}")
    
    # 1. Check mode detection
    mode, date = detect_retrieval_mode(query)
    print(f"  Mode detected: {mode.value}")
    
    # 2. Check domain inference
    domains = infer_query_domains(query)
    print(f"  Domains inferred: {domains}")
    
    # 3. Run search
    try:
        results = search_memory(query, k=10)
        print(f"  Results count: {len(results)}")
        
        # Group by domain
        domain_counts = {}
        for r in results:
            d = r.domain or "unknown"
            domain_counts[d] = domain_counts.get(d, 0) + 1
        
        print(f"  Domain distribution:")
        for d, c in sorted(domain_counts.items(), key=lambda x: -x[1]):
            print(f"    {d}: {c}")
        
        # Check if core appears
        core_count = domain_counts.get("jarvis.core", 0) + domain_counts.get("jarvis-core", 0)
        print(f"  Core docs in results: {core_count}")
        
        # Show top 3 results
        print(f"  Top 3 results:")
        for i, r in enumerate(results[:3]):
            print(f"    {i+1}. domain={r.domain} score={r.score:.3f}")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    print()

print("=== DONE ===")
