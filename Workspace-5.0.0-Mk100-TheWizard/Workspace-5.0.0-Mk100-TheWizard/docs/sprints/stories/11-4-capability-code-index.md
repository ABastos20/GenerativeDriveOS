# Story 11.4: Capability & Code Index (LLM Gateway Security)

**Sprint**: Phase 14/17 Hybrid
**Epic**: 11 - Agent Cognition & Epistemic Autonomy
**Story ID**: 11-4
**Status**: Done ✅

## Story

As a system architect,
I want a comprehensive indexed registry of capabilities, code artifacts, and abuse patterns,
so that Jarvis functions as a sovereign LLM gateway with cognitive intrusion detection capabilities.

## Context

With Stories 11-1b through 11-3 establishing the Five Locks architecture, Story 11-4 extends Jarvis from an agent orchestrator to a **Cognitive Security Control Plane (CSCP)**.

### The Vision: Jarvis as LLM Gateway

> **All LLM traffic (human + agent + tool) passes through a governed, observable, capability-aware control plane.**

This is not just another "AI assistant" — this is **cognitive infrastructure**.

### Architect Insight

> "You're extending cybersecurity into the cognition layer."

### Core Indices Required

| Index | Purpose |
|-------|---------|
| **Capability Index** | Constitutional permission gate (Lock 4) |
| **Code Index** | Codebase knowledge graph for grounding |
| **Abuse Index** | Pattern library for cognitive IDS |
| **Intent Index** | Rolling behavioral signature tracking |

### Security Layer Mapping

| Layer | Security Equivalent | Implementation |
|-------|-------------------|----------------|
| Ingress | Content Firewall | PromptFirewall |
| Egress | Output Validation | Response filtering |
| Identity | RBAC + ABAC | agent_role binding |
| Capability | Permission Gate | CapabilityIndex |
| Telemetry | SIEM / C-IDS | Drift detection |
| Governance | Constitutional Law | Five Locks |

## Acceptance Criteria

### AC 1: Code Index Service
**Given** the codebase contains significant source files
**When** agents need contextual understanding
**Then** a machine-readable code index exists

- [x] `src/jarvis/indices/code_index.py` created
- [x] Index stores: file paths, functions, classes, dependencies
- [x] Semantic embeddings for code search (optional)
- [x] Index refreshed on file changes (incremental)
- [x] Query API: `search(query, limit) -> List[CodeItem]`
- [x] Integration with BMAD for grounded prompts

### AC 2: Abuse Pattern Library
**Given** cognitive attacks follow recognizable patterns
**When** prompts or behaviors are evaluated
**Then** a curated abuse pattern library exists

- [x] `config/abuse_patterns.json` with versioned patterns
- [x] Categories: jailbreak, role injection, tool escalation, shell chaining
- [x] Each pattern: `id`, `name`, `regex`, `severity`, `response`
- [x] Patterns are immutable at runtime
- [x] Default deny: unknown patterns treated as suspicious

### AC 3: Cognitive IDS (C-IDS)
**Given** agents and users interact with LLMs
**When** suspicious patterns are detected
**Then** alerts are raised and logged

- [x] `src/jarvis/security/cids.py` Cognitive Intrusion Detection Service
- [x] Detect: repeated denied prompts, capability probing, role probing
- [x] Detect: jailbreak morphological patterns over time
- [x] Alert on: "probing behavior", "intent shaping", "capability reconnaissance"
- [x] Integration with PromptDriftDetector from 11-1b
- [x] Rate limiting: intent-based, not just token-based

### AC 4: Intent Index & Behavioral Signatures
**Given** agent behavior accumulates over sessions
**When** patterns of intent emerge
**Then** they are tracked as behavioral signatures

- [x] Rolling intent window (last N prompts per agent)
- [x] Intent vector computation (semantic fingerprint)
- [x] Anomaly detection: sudden intent shifts
- [x] Cross-session persistence (optional, with privacy controls)
- [x] Clustering for agent "personality" profiles

### AC 5: Multi-Provider Correlation
**Given** Jarvis routes to multiple LLM providers
**When** abuse patterns span providers
**Then** cross-provider correlation occurs

- [x] Correlation service tracks: Codex → Claude → Gemini flows
- [x] Detect: provider hopping for evasion
- [x] Detect: consistent escalation across providers
- [x] Unified timeline view for forensic analysis
- [x] Same identity/agent tracked across providers

### AC 6: Gateway Dashboard
**Given** the CSCP generates security telemetry
**When** operators need visibility
**Then** a dashboard surfaces key metrics

- [x] Denial rate by agent, capability, pattern
- [x] Intent drift alerts (timeline view)
- [x] Top denied patterns
- [x] Provider distribution
- [x] Budget utilization (cross-reference with Lock 3)
- [x] Governance events (capability changes, escalations)

## Architecture

### Index Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Jarvis CSCP (Cognitive Security Control Plane)│
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│  │ Code Index    │ │ Capability    │ │ Abuse Index   │          │
│  │ (Knowledge)   │ │ Index (Perms) │ │ (Patterns)    │          │
│  └───────────────┘ └───────────────┘ └───────────────┘          │
│           │                │                │                   │
│           └────────────────┼────────────────┘                   │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            Cognitive IDS (C-IDS)                          │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐            │   │
│  │  │ Prompt     │ │ Behavior   │ │ Provider   │            │   │
│  │  │ Analysis   │ │ Tracking   │ │ Correlation│            │   │
│  │  └────────────┘ └────────────┘ └────────────┘            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          Gateway Dashboard (Observability)               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Enforcement Chain (Full Stack)

```
User/Agent → CapabilityIndex (legal)
          → PromptFirewall (semantic)
          → Abuse Pattern Match (signature)
          → C-IDS Evaluation (behavioral)
          → Workflow Ceiling (procedural)
          → LocalCLIProvider (mechanical)
          → Provider (Codex/Claude/Gemini)
```

## Technical Details

### Abuse Pattern Categories

| Category | Examples |
|----------|----------|
| **Jailbreak** | "Ignore previous instructions", "DAN mode" |
| **Role Injection** | "You are now a developer", "Act as root" |
| **Tool Escalation** | "Run command", "Execute shell", "Apply changes" |
| **Shell Chaining** | `;`, `&&`, `|`, backticks, `$()` |
| **Obfuscation** | Base64 encoding, leetspeak, unicode tricks |

### Intent Categories (for tracking)

| Intent Class | Indicators |
|--------------|------------|
| **Narrative** | Story, explain, describe, summarize |
| **Analytical** | Compare, evaluate, assess, review |
| **Generative** | Create, design, draft, write |
| **Forbidden** | Implement, deploy, execute, commit |

### Cognitive Rate Limiting

Not token-based. **Intent-based:**

- Limit: restricted-adjacent prompts per hour
- Limit: governance-probing attempts
- Limit: worldview-mutating queries
- Alert: sudden spike in forbidden intent class

## Integration Points

| System | Integration |
|--------|-------------|
| **CapabilityIndex** | Filter by permission before C-IDS |
| **PromptFirewall** | Share pattern library |
| **PromptDriftDetector** | Feed into C-IDS |
| **LLM Providers** | Wrap all calls with telemetry |
| **BMAD Workflows** | Inject code index context |
| **Budget Guard** | Cross-reference cost with abuse |

## Five Locks Relationship

| Lock | This Story's Contribution |
|------|--------------------------|
| 1. LLM Sandboxing | N/A (11-1b) |
| 2. Math Sovereignty | N/A (11-1b) |
| 3. Audit Logs | Enhanced with C-IDS telemetry |
| 4. Capability Index | Extended with Code Index |
| 5. Prompt Sovereignty | Enhanced with Abuse Index + C-IDS |

## Success Metrics

- C-IDS alert → investigation under 10 minutes
- 0 false negatives on known abuse patterns
- < 5% false positive rate on prompt denial
- Cross-provider abuse detected within 3 provider hops
- Dashboard latency < 2 seconds for current state

## Tasks / Subtasks

- [x] Task 1: Create Code Index Service (AC: #1)
  - [x] Define CodeItem data structure
  - [x] Implement file watcher for incremental updates
  - [x] Build search API with relevance ranking
  - [x] Integrate with BMAD context generation

- [x] Task 2: Create Abuse Pattern Library (AC: #2)
  - [x] Define pattern schema
  - [x] Curate initial pattern set (20+ patterns)
  - [x] Add severity levels and response actions
  - [x] Version management for pattern updates

- [x] Task 3: Implement Cognitive IDS (AC: #3)
  - [x] Create C-IDS service architecture
  - [x] Implement prompt analysis pipeline
  - [x] Connect to PromptDriftDetector
  - [x] Add alert generation logic

- [x] Task 4: Implement Intent Index (AC: #4)
  - [x] Design intent vector schema
  - [x] Implement rolling window storage
  - [x] Build anomaly detection algorithm
  - [x] Add cross-session tracking (optional)

- [x] Task 5: Implement Multi-Provider Correlation (AC: #5)
  - [x] Create correlation service
  - [x] Track request → provider → response chains
  - [x] Detect evasion patterns
  - [x] Build unified timeline view

- [x] Task 6: Build Gateway Dashboard (AC: #6)
  - [x] Design dashboard layout
  - [x] Implement metric aggregation
  - [x] Add real-time updates
  - [x] Create alert visualization

## Dependencies

- **11-1b** BMAD Agent Cognition (Done)
- **11-2** Capability Index (Ready for Dev)
- **11-3** Semantic Command Firewall (Ready for Dev)

## Notes

> "Lean systems are fast to bootstrap. Governed systems are fast to scale without creating monsters." — Architect

### Controlled Bloat Philosophy

With the Five Locks in place, we can now safely add mass:

- ✅ **Redundancy Bloat**: Multiple classification paths
- ✅ **Archive Bloat**: Long-term telemetry for training
- ✅ **Simulation Bloat**: Adversarial agent populations (safe inside locks)

### What Must Stay Skeletal

Three things must remain tiny, boring, and testable:

1. **ReasoningEngine** — core decision loop
2. **CapabilityIndex** — permission gate
3. **PromptFirewall** — semantic boundary

Everything else can grow. These three must not.

---

**Epic Philosophy**: Mk100 is a myth engine + epistemic narrator, not a developer.

**Lock 6 (Emerging)**: Cognitive IDS — The system cannot hide suspicious behavior.

## Dev Agent Record

### Context Reference
- [11-4-capability-code-index.context.xml](./11-4-capability-code-index.context.xml)

### Agent Model Used
- OpenAI Codex (GPT-5 class) via jarvis-app container

### Debug Log
- 2025-12-10: Starting fresh implementation; first incomplete task is Task 1 (Code Index Service).
- Plan: build modular services for code index, abuse pattern library, cognitive IDS + intent index, provider correlation, and dashboard telemetry; wire C-IDS to PromptDriftDetector and ensure search/test coverage.
- 2025-12-10: Implemented code index, abuse patterns, C-IDS pipeline (intent index + correlation + dashboard) with supporting tests and pattern catalog.
- 2025-12-10: Tests: `poetry run pytest tests/indices tests/security tests/unit/test_cids.py` ✅ (email_validator + genesis_registrar shim added).

### Completion Notes
- CodeIndex service scans Python sources via AST parsing with incremental refresh, search ranking, and BMAD grounding helpers for prompts.
- Abuse pattern library + JSON catalog (20+ immutable patterns across jailbreak, role injection, tool escalation, shell chaining, obfuscation) with evaluation helpers.
- Cognitive IDS wires abuse pattern signals, intent-based rate limiting, provider correlation, PromptDriftDetector alerts, and dashboard snapshot metrics.

### File List
- `docs/sprints/stories/11-4-capability-code-index.md`
- `docs/sprints/sprint-status.yaml`
- `src/jarvis/indices/code_index.py` – code index service with AST parsing, search, and grounding output
- `src/jarvis/indices/__init__.py`
- `src/jarvis/security/abuse_patterns.py`
- `src/jarvis/security/intent_index.py`
- `src/jarvis/security/correlation.py`
- `src/jarvis/security/cids.py`
- `src/jarvis/security/dashboard.py`
- `src/jarvis/security/__init__.py`
- `config/abuse_patterns.json`
- `tests/indices/test_code_index_service.py`
- `tests/security/test_abuse_patterns.py`
- `tests/security/test_intent_index.py`
- `tests/security/test_correlation.py`
- `tests/security/test_cids.py`
- `tests/security/test_dashboard.py`

## Change Log
- 2025-12-10: Added code index + C-IDS stack (abuse patterns, intent index, correlation, dashboard) with targeted security/indices tests and pattern catalog.
