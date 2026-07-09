# Remaining Violations - Action Plan

## Status: 15 violations remaining

Based on linter output and analysis, here are the remaining violations and action plan:

### HIGH PRIORITY - Complexity Violations (7)

1. **GoogleAIProvider.call()** - Complexity 23 (already partially refactored, needs more)
   - File: `src/jarvis/llm/providers.py`
   - Current: 119 LOC, complexity 23
   - Action: Extract `_configure_sdk()`, `_build_generation_config()` methods
   - Target: Complexity ≤15

2. **ChatController** - Complexity 51  
   - File: `src/jarvis/controllers/chat_controller.py`
   - Action: Apply dataflow boundaries, split `process_chat` orchestrator
   - Target: Complexity ≤15

3. **ARCHESController** - Complexity 85, 21 methods
   - File: TBD (find it)
   - Action: DEFER to Phase 3 (requires ArchesState extraction first per architect notes)
   
4. **PersonaDB** - Complexity 23
   - File: `src/jarvis/agents/persona_db.py`
   - Action: Extract 2-3 helper methods
   - Target: Complexity ≤15

5. **HealthMonitor** - Complexity 23
   - File: TBD (find it)
   - Action: Extract helper methods
   - Target: Complexity ≤15

6. **ResearchPlanner** - Complexity 17 
   - File: TBD (find it)
   - Action: Extract 1-2 helpers
   - Target: Complexity ≤15

7. **JarvisFileEventHandler** - Complexity 17
   - File: TBD (find it)  
   - Action: Extract 1-2 helpers
   - Target: Complexity ≤15

### MEDIUM PRIORITY - Function LOC Violations (6)

8. **_heuristic_metadata_from_payload** - 190 LOC
   - File: TBD (likely in memory or ingestion)
   - Action: Apply semantic phase splitting (validate→extract→heuristics→fallback)

9. **catalog_documents** - 230 LOC
   - File: TBD
   - Action: Split by batch phases (discover→filter→batch_ingest)

10. **ingest_file** - 178 LOC  
    - File: TBD
    - Action: Apply semantic phases (validate→normalize→classify→persist)

11. **query** - 667 LOC (CLI)
    - File: TBD
    - Action: AgentQueryRunner pattern (parse→execute→render)

12-13. **Unknown function LOC violations** (2 more)
    - Need to identify from linter output

### LOW PRIORITY - Deferred

14. **ARCHESController.methods** - 21 methods (> 20 limit)
    - Action: DEFER - needs state extraction first

15. **Unknown file LOC** - One file >800 LOC  
    - Action: Identify and assess

## Execution Strategy

**Phase 1** (This session): Quick wins
- GoogleAIProvider complexity reduction
- PersonaDB, ResearchPlanner, JarvisFileEventHandler (simple extractions)
- Target: 15 → 10 violations

**Phase 2** (Next): Medium complexity
- ChatController dataflow refactor  
- Function LOC violations (heuristic, catalog, ingest, query)
- Target: 10 → 3 violations  

**Phase 3** (Future/Story 8-7): Architectural
- ARCHESController (after ArchesState extraction)
- Large file LOC
- Target: 3 → 0 violations

## Success Metrics
- All files ≤600 LOC (agent-editable)
- All classes ≤15 complexity
- All functions ≤120 LOC
- All classes ≤20 methods
- Zero violations → v2.0.0 tag \ready
