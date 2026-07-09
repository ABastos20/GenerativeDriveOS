"""BMAD Method domain mappings.

Covers BMAD methodology, workflows, agents, patterns, and project management
artifacts (epics, stories, sprints, retrospectives).

Note: Many path-based heuristics for BMAD are in domain_catalog.py (lines 195-243)
since they rely on folder structure (docs/sprints/, .bmad/bmm/, etc.).
"""

from __future__ import annotations

from typing import Dict

# Keyword-based classification for BMAD Method
BMAD_KEYWORD_MAP: Dict[str, str] = {
    # BMAD Method General (existing from old map)
    "bm ad": "bmad.method",
    "bmad": "bmad.method",
    "bmad method": "bmad.method",
    "bmad methodology": "bmad.method",

    # BMAD Workflows
    "bmad workflow": "bmad.workflows",
    "create-agent": "bmad.workflows",
    "create-workflow": "bmad.workflows",
    "create-module": "bmad.workflows",
    "edit-agent": "bmad.workflows",
    "workflow-status": "bmad.workflows",

    # BMAD Agents
    "bmad agent": "bmad.agents",
    "expert agent": "bmad.agents",
    "simple agent": "bmad.agents",
    "module agent": "bmad.agents",
    "agent architecture": "bmad.agents",

    # BMAD Builder
    "bmad builder": "bmad.builder",
    "bmad-builder": "bmad.builder",
    "agent compilation": "bmad.builder",

    # BMAD Patterns
    "bmad pattern": "bmad.patterns",
    "agent pattern": "bmad.patterns",
    "workflow pattern": "bmad.patterns",

    # Project Management (existing from path heuristics but adding keywords)
    "epic ": "project.epic",
    "user story": "project.story",
    "story ": "project.story",
    "sprint": "project.sprints",
    "sprint planning": "project.sprints",
    "retrospective": "project.retrospective",
    "retro ": "project.retrospective",
    "agile": "project.agile",
}
