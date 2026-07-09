# Epic 11: Sovereign Identity Layer

**Status:** Planning 📋
**Goal:** Establish cryptographic, OIDC-compliant identity for all governance actors to ensure legal attributability and enable safe Epistemic Autonomy.

---

## Architect Notes (The "Legitimacy First" Mandate)

> "Identity is sovereign. Governance is zero-knowledge."

Before we can safely activate **Epistemic Autonomy (Phase 9)**, the system must know *who* is pulling the strings.
"Mock users" with header-based auth (`X-User-ID`) are forgeable and legally null.
We must transition to **Regulator-Grade Identity**:
1.  **Cryptographic Proof**: Identity proven via OIDC/JWT signed by a trusted issuer.
2.  **Privacy by Design**: Governance DB stores *no PII*, only opaque subject IDs (`sub`).
3.  **Sovereignty**: We must own a Mock IdP to simulate this offline or in sovereign deployments.

---

## Story Breakdown

### 11-1: Sovereign Identity Transformation
- **Goal**: Architect the OIDC-compliant identity layer and Zero-PII database split.
- **Mechanism**:
    - **Mock IdP**: A standalone service (in-repo) that issues valid, signed JWTs.
    - **DB Split**: `governance_identities` (Core) vs `idp_users` (PII).
    - **Auth Middleware**: Verify JWTs (`iss`, `aud`, `exp`) instead of trusting headers.
- **Deliverables**:
    - `src/jarvis/idp` (Key rotation, Token issuance)
    - Schema migration (Drop PII columns, add `subject_id`)
    - Updated `bootstrap_governance.py`

### 11-2: Identity Federation (Future)
- **Goal**: Connect to real external IdPs (GitHub, Google, EU Login).
- **Checklist**:
    - [ ] Configure multiple OIDC issuers in `Constitution`.
    - [ ] Map external claims (e.g., GitHub Teams) to Governance Roles.

---

## Technical Architecture

### The Data Split

**A. Sovereign Identity Boundary (IdP Side)**
*Contains PII. Isolated.*
```sql
TABLE idp_users (
    id UUID PRIMARY KEY,
    subject_id VARCHAR NOT NULL, -- Public OIDC sub
    email VARCHAR ENCRYPTED,
    name VARCHAR ENCRYPTED,
    password_hash VARCHAR -- If using local auth
);
```

**B. Governance Core (Zero-PII)**
*GDPR-safe. Cryptographic.*
```sql
TABLE governance_identities (
    id UUID PRIMARY KEY,
    subject_id VARCHAR NOT NULL, -- Link to OIDC Token
    issuer VARCHAR NOT NULL,     -- e.g., "https://idp.jarvis.corp"
    role VARCHAR NOT NULL,
    trust_score_id UUID,
    is_active BOOLEAN
);
```

### The Auth Flow (JWT)

1.  **Client** (Frontend) -> `POST /auth/token` (IdP) -> **JWT**
2.  **Client** -> `POST /api/governance/vote` (Core)
    *   Header: `Authorization: Bearer <JWT>`
3.  **Core Middleware**:
    *   Verify Signature (using IdP Public Key)
    *   Extract `sub` (Subject ID) from claims
    *   Lookup `governance_identities` where `subject_id == sub`
    *   **result**: Authenticated Actor (without ever seeing email/name)

---

## Execution Plan

1.  **Mock IdP Kernel**: Build the token issuer first so we can generate valid test tokens.
2.  **Schema Migration**: Refactor the DB while preserving existing trust scores (map by ID).
3.  **Middleware Switch**: Deprecate `X-User-ID`, enforce `Bearer` token.
4.  **Frontend Update**: Update `governance.js` to perform login flow (or auto-login in dev).

---

## Why This Matters

*   **Legal Attributability**: Votes are signed. Escalations are proven.
*   **GDPR Compliance**: Governance core is toxic-waste (PII) free.
*   **Simulation Realism**: We can simulate 10,000 distinct cryptographic actors.
*   **Phase 9 Safety**: Autonomy requires a clear "Human-in-the-loop" signal. This provides the "Human" part securely.

---

## Dependencies

### Depends On
- **Epic 9**: Governance Model (Roles, Trust Scores)

### Enables
- **Phase 9**: Epistemic Autonomy (Safe Activation)
- **Epic 14**: Large Scale Simulation
- **Regulatory Certification**

---

**Motto**: "Identity is sovereign. Governance is zero-knowledge."
