# Antigravity Workspace

This directory contains configuration, scripts, and context files specific to the **Antigravity** agent (Gemini).

## Purpose
To optimize Antigravity's workflow within the BMAD method without interfering with:
- **Claude** (`.claude/`)
- **Codex** (`.codex/`)
- **Jarvis** (Core System)

## Structure
- `scripts/`: Helper scripts for context loading, status checks, and automation.
- `playbooks/`: BMAD-aligned procedure documents for common tasks.
- `memory/`: (Optional) Temporary scratchpad for complex reasoning chains.

## Usage
Scripts in this directory are intended to be run by Antigravity via `run_command` to speed up context gathering and verification.
