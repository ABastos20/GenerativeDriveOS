# GenerativeDrive Overview

This document captures the working overview of **GenerativeDrive (GD)**, distilled from GPT exports (see `docs/jarvis/conversation-index.md` core threads) and local intent. It is a living spec and will evolve.

## Vision

GenerativeDrive is a long-horizon, systems-level project to:

- Turn the **interior of Portugal** into a net energy producer, where each house is both **client and producer**.
- Minimise:
  - Time energy spends on large grids.
  - Physical distance energy must travel.
- Use:
  - **Batteries** as short/medium-term cache.
  - **Hydrogen** as long-duration storage (“battery”).
  - **Smart grids + telemetry** as the coordination fabric.
  - **AI (Jarvis)** as the brain for prediction, optimisation, and orchestration.

Jarvis’ eventual role: constitutional layer and co-pilot for GD, coordinating agents across energy, data, infra, and strategy.

## Core Components

- **Decentralised Local Cells**
  - Roughly 1000-house clusters.
  - Local generation (solar, other renewables).
  - Local storage (batteries, hydrogen).
  - Local control loop (smart grid, telemetry, AI).

- **National Backbone**
  - Integration with nodes like **Sines** (ports, industrial/energy hubs).
  - Interfaces with utilities/partners (e.g., Galp, others).
  - Regulatory, grid, and market integration.

- **Telemetry & Smart Grid**
  - High-frequency measurement of consumption, production, and grid health.
  - Networked devices (routers/switches, sensors) feeding into a unified model.
  - Secure, resilient telemetry pipelines (TLS, proper capacity sizing).

- **AI Knowledge Centre**
  - Jarvis-centric RAG/memory expected to:
    - Store and retrieve GD models, reports, investor decks, and simulations.
    - Support scenario analysis (technical, economic, geopolitical).
    - Orchestrate specialised agents (e.g., energy planner, infra architect).

## Themes & Threads

Key conversation themes reflected in `conversation-index.md`:

- Energy partnerships and GTM (Galp, BloombergNEF, etc.).
- Hydrogen economics and practicalities (Mirai filling, Iberdrola pricing, solar+H2 models).
- Smart grid and telemetry (Nokia SR OS, Cisco telemetry, RAM/CPU needs).
- Geography and logistics (interior Portugal, Sines, hub ports like Singapore).

These are elaborated in dedicated playbooks under `docs/jarvis/playbooks/`.

## Jarvis Responsibilities (High-Level)

- Maintain a **coherent mental model** of GD across:
  - Tech architecture.
  - Energy systems.
  - Partnerships and business models.
  - Time horizons (years to decades).
- Help the architect (Ariel) by:
  - Keeping pace realistic (enterprise vs personal speed).
  - Translating long-term vision into concrete steps and artifacts.
  - Ensuring changes in this repo keep GD as the north star.

