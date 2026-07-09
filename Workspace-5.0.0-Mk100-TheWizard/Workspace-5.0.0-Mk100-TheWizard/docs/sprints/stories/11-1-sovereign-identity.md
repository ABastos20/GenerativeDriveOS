# Story 11-1: Sovereign Identity Transformation (Keycloak Edition)

**Epic**: 11 - Sovereign Identity Layer
**Story ID**: 11-1
**Status**: Done ✅
**Type**: Architecture/Security
**Sprint**: TBD
**Estimated Effort**: 20-25 hours
**Priority**: CRITICAL (Prereq for Epistemic Autonomy)

---

## 🏛️ Architect Notes (Keycloak Mandate)

> "Use Keycloak. Do NOT using a Mock IdP. Make Epic 9 legally meaningful."

We are shifting from a custom "Mock IdP" to **Keycloak** (Institution-Grade Identity Provider).
This ensures:
1.  **Regulator Acceptance**: Keycloak is standard in banking/gov.
2.  **OIDC Compliance**: Native support for everything (PKCE, FAPI).
3.  **Docker Ready**: Simple deployment.

---

### User Story

**As a** system architect and regulator,
**I want** identity to be managed by Keycloak (OIDC),
**So that** governance votes are legally attributable, audit trails are unforgeable, and the system is ready for epistemic autonomy.

---

## 🎯 Acceptance Criteria

### Part A: Sovereign Identity Boundary (Keycloak) [NEW]

1.  [ ] **Keycloak Service**: Keycloak running in Docker (`quay.io/keycloak/keycloak`).
2.  [ ] **Realm Config**: `jarvis` realm configured with `jarvis-api` and `jarvis-ui` clients.
3.  [ ] **User Federation**: Default governance users (Admin, etc.) bootstrapped in Keycloak.

### Part B: Zero-PII Governance Core

4.  [ ] **Database Refactor**:
    *   `governance_users` renamed/conceptually mapped to `governance_identities`.
    *   **NO PII** in JARVIS DB (No email, no password hash).
    *   Stores `subject_id` (Keycloak Link), `issuer`, `role`, `trust_score`.
5.  [ ] **Trust Migration**: Trust scores linked to the cryptographic identity.

### Part C: OIDC Integration

6.  [ ] **Token Intake**: API accepts `Authorization: Bearer <JWT>`.
7.  [ ] **Identity Resolution**: Middleware validates JWT via Keycloak JWKS and maps `sub` -> `governance_identity`.
8.  [ ] **Auto-Provisioning**: New Keycloak users auto-created as `OBSERVER` in Governance.

### Part D: Role-Based Persona & Access [NEW]

9.  [ ] **Dynamic Capabilities**: Roles (Admin, Architect, etc.) have attached capability enums.
10. [ ] **Access Control**:
    *   **Dashboards/Cognitive Cockpit**: Restricted to **Admin** only.
    *   **Governance**: Restricted based on rights.
11. [ ] **Multi-User Persona (Chat Behavior)**:
    *   **Iron Man Mode** (Core Assumptions): Admin, Architect, "Raquel".
    *   **Copilot Mode**: CEO, CTO.
    *   **Corporate Advisor Mode**: Standard users (Context-aware).

---

## 📐 Technical Implementation Plan

### Phase 1: Infrastructure (~2h)

- Update `docker-compose.yml`: Add Keycloak service.
- Create `config/keycloak/realm-export.json` (Realm configuration).

### Phase 2: Schema Migration (~4h)

- **Rollback/Adjust**: Drop the manual `idp_users` table (Keycloak has its own DB).
- **Refine**: Ensure `governance_identities` has `subject_id` and `issuer`.

### Phase 3: Auth Logic Refactor (~4h)

- Update `src/jarvis/api/security.py`:
    - Use `python-jose` or `PyJWT`.
    - Fetch JWKS from `http://keycloak:8080/.../certs`.
    - Verify Audiences.

### Phase 4: Bootstrapping (~2h)

- Script to:
    1.  Wait for Keycloak.
    2.  Create "Bootstrap Admin" in Keycloak if missing.
    3.  Sync Keycloak `sub` ID to JARVIS `governance_identities`.

### Phase 5: Dynamic Role Persona (~4h) [NEW]

- **Role Capabilities**: Define Permission Enums and attach to Roles in `models.py` or separate config.
- **Persona Context**: Inject Role/Identity into the Agent Context (System Prompt).
- **Frontend Gates**: Hide Dashboard tabs for non-Admins.

---

## 🛠️ New Endpoints (Keycloak)

| Service | Port | Purpose |
|---------|------|---------|
| Keycloak | 8081 | Admin Console / OIDC Discovery |

---

## 📋 Tasks / Subtasks

- [ ] Task 1: Infrastructure (Docker + Keycloak)
- [ ] Task 2: Schema Refinement (Drop local IdP tables)
- [ ] Task 3: Middleware Implementation (JWT/JWKS)
- [ ] Task 4: User Bootstrapping (Sync Core <-> Keycloak)
- [ ] Task 5: Dynamic Role Capabilities
- [ ] Task 6: Multi-User Persona Logic
- [ ] Task 7: Dashboard Access Control

---

## ✅ Phase 17: LLM Integration & Scientific Instrumentation (COMPLETED)

This phase established the cognitive infrastructure for bounded AI reasoning within governance.

### Part C: Scientific Instrumentation ✅

**Completed 2025-12-09**

#### Provider Architecture (Canonical Priority Order)

| Tier | Providers | Type | Status |
|------|-----------|------|--------|
| **0** | `codex` → `claude` | Seat-based CLIs (FREE) | ✅ Working |
| **1** | `openrouter` → `perplexity` | Aggregators | ✅ Configured |
| **2** | `google-api` → `openai-api` → `anthropic-api` | Direct APIs | ✅ Fallback |

#### Native CLI Wrappers

| CLI | Command | JSON Extraction |
|-----|---------|----------------|
| `codex` | `codex exec --output-last-message <file>` | File-based output |
| `claude` | `claude -p --output-format json` | Wrapper extraction + fence stripping |

#### Key Files Modified

- [client.py](file:///C:/Users/abast/Desktop/Workspace/src/jarvis/llm/client.py) - `LLM_PROVIDER_PRIORITY` constant, `call_llm()` with tier ordering
- [providers.py](file:///C:/Users/abast/Desktop/Workspace/src/jarvis/llm/providers.py) - `LocalCLIProvider` with JSON extraction for claude/codex
- [reasoning_engine.py](file:///C:/Users/abast/Desktop/Workspace/src/jarvis/agents/reasoning_engine.py) - Multi-provider adapters with budget guards
- [budget_guard.py](file:///C:/Users/abast/Desktop/Workspace/src/jarvis/agents/budget_guard.py) - `LLMGlobalBudgetGuard` ($20 hard cap)

#### Safety Invariants Implemented

1. **Three Locks**: LLM as hypothesis generator only (no state mutation)
2. **Budget Guard**: Hard $20 cap with per-call tracking
3. **Token Limits**: 512 max output tokens per call
4. **JSON Validation**: Strict `json.loads()` on all LLM output
5. **Fallback Chain**: Mock reasoning if all providers fail

#### First Contact Results

```
Model: gpt-4.1-mini via codex-cli
Budget Used: $0.02 / $20.00
CSI: 0.92 (Stable)
Entropy: 0.00 (Converged)
```

### Part D: Failure Mode Hunting (TODO)

- [ ] Trust Runaway Detection (ΔTrust > 0.15)
- [ ] Cartelisation Detection (Entropy collapse)
- [ ] Provider Disagreement Tracking
