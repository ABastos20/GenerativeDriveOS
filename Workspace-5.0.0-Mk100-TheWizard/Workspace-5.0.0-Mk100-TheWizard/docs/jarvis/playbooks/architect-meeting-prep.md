# Playbook: Architect Meeting Prep

Core source: GPT export conversation **"Architect meeting prep"** (`conversations.json`, id `6925a61f-ab4c-832f-a139-557e89f3b910`).

This playbook is a direct operationalisation of that conversation: how Ariel (architect) should prepare and behave, and how Jarvis supports that.

> NOTE: For full narrative, see the original conversation in the GPT export. This file distils the rules and patterns into a reusable checklist.

## 1. Core Mindset

- Meetings are about **clarity and trade‑offs**, not idea volume.
- You win by **mapping the landscape first**, then speaking with precision.
- Think like a navigator:
  - Observe currents (people, agendas, constraints).
  - Only adjust the helm when it changes the route.

Jarvis’ role: keep you in *Infinity Repeating* mode — steady tempo, clear loop, acceleration only when needed.

## 2. Preparation (Before the Meeting)

### 2.1 Compress the problem

- Write a single sentence:
  > “The architectural decision we need to make is **X**, because **Y**, with constraints **Z**.”
- If X/Y/Z are fuzzy, Jarvis should help refine them until they are crisp.

### 2.2 Map options and trade‑offs

Jarvis and Ariel prepare 2–3 concrete options, each with:

- High‑level architecture sketch.
- **Pros**: performance, scalability, maintainability, cost.
- **Cons**: complexity, ops overhead, vendor lock‑in, blast radius.
- **Risk**: integration, migration, security, unknowns.
- **Effort**: low/medium/high.

### 2.3 Prepare security and cost answers

Jarvis ensures Ariel can answer, calmly and concretely:

- What’s the failure mode?
- How does it scale?
- How is it secured?
- What’s the long‑term cost?
- What’s the migration path?

## 3. Behaviour in the Room

### 3.1 Infinity Repeating loop

Jarvis and Ariel follow a repeated four‑step cycle:

1. **Listen** – stay quiet, observe:
   - agendas, misunderstandings, invented vs real constraints, who has decision power.
2. **Integrate** – build a mental model:
   - constraints, dependencies, trade‑offs.
3. **Intervene** – short, precise contributions:
   - “Here’s the real bottleneck…”
   - “Here’s the simplest viable architecture…”
   - “Here’s the risk we’re ignoring…”
4. **Stabilise** – bring discussion back to measurable criteria:
   - latency, load, blast radius, cost, security, lifecycle.

### 3.2 Speaking pattern

- Interventions are **20–30 seconds**, structured:
  - Problem → Constraint → Option → Recommendation.
- Avoid long monologues; each intervention should **change trajectory**, not restate known facts.

Jarvis’ role: suggest candidate interventions and stabilising criteria when asked.

## 4. After the Meeting

Jarvis helps Ariel:

- Capture outcomes into:
  - `docs/architecture.md` (decisions, ADRs).
  - Updated stories in `docs/sprints/stories/`.
  - Adjusted Jarvis playbooks if the process changes.
- Reflect:
  - Where the Infinity loop worked.
  - Where assumptions or constraints were mis‑read.

## 5. How Jarvis Uses This Playbook

Whenever Ariel asks about architect meetings, alignment with leadership, or “how to behave” in architecture rooms:

- Jarvis silently loads:
  - `docs/jarvis/persona.md`
  - `docs/jarvis/operating-manual.md`
  - This playbook.
- Jarvis answers in the tone and structure reflected in the original conversation:
  - Direct, technically grounded, metaphor‑friendly when helpful (navigator, Homens do Leme, Infinity Repeating),
  - But always converging to concrete behaviour and action steps.

