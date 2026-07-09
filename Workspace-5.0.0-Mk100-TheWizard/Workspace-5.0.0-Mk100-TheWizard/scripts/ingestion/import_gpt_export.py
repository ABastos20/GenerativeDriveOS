"""Import GPT export data into Jarvis docs.

Usage (from repo root):
    python scripts/import_gpt_export.py

This script:
- Reads GPT export JSON files under docs/gpt export/
- Generates or refreshes summary docs under docs/jarvis/
  - personas, conversation index, and playbook seeds

It is intentionally conservative: it does not attempt to summarize
large conversations automatically, but it builds an index you can
curate by hand.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional


EXPORT_DIR = Path("docs") / "gpt export"
JARVIS_DIR = Path("docs") / "jarvis"


@dataclass
class ConversationIndexEntry:
    title: str
    created_at: Optional[str]
    id: Optional[str]
    is_core: bool = False


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


CORE_KEYWORDS = [
    "architect meeting prep",
    "jarvis ai knowledge centre",
    "jarvis",
    "j.a.r.v.i.s"
    "jarvis ai knowledge center",
    "water-loop",
    "smart-grid",
    "telemetry",
    "nossis",
    "generativedrive",
    "generative drive",
    "gd",
    "ntt",
    "gap",
    "hydrogen",
]


def index_jarvis_conversations(conversations: Any) -> List[ConversationIndexEntry]:
    """Extract a lightweight index of Jarvis/architecture-related conversations.

    Core conversations:
    - Titles matching any CORE_KEYWORDS (case-insensitive)
    """
    entries: List[ConversationIndexEntry] = []
    if not isinstance(conversations, list):
        return entries

    for item in conversations:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        lower_title = title.lower()
        if not any(k in lower_title for k in CORE_KEYWORDS) and "jarvis" not in lower_title:
            continue
        created_at = item.get("create_time") or item.get("created_at")
        conv_id = item.get("id")
        entries.append(
            ConversationIndexEntry(
                title=title,
                created_at=str(created_at) if created_at is not None else None,
                id=str(conv_id) if conv_id is not None else None,
                is_core=any(k in lower_title for k in CORE_KEYWORDS),
            )
        )
    return entries


def write_conversation_index(entries: List[ConversationIndexEntry]) -> None:
    target = JARVIS_DIR / "conversation-index.md"
    lines: List[str] = [
        "# Jarvis Conversation Index",
        "",
        "Jarvis‑related threads imported from GPT export (`docs/gpt export/conversations.json`).",
        "",
        "This index is a starting point for curating playbooks and decisions.",
        "",
    ]
    if not entries:
        lines.append("_No Jarvis‑titled conversations found in export._")
    else:
        core_entries = [e for e in entries if e.is_core]
        if core_entries:
            lines.append("## Core Threads (Architect Meeting Prep)")
            lines.append("")
            for entry in core_entries:
                meta = []
                if entry.created_at:
                    meta.append(f"created: `{entry.created_at}`")
                if entry.id:
                    meta.append(f"id: `{entry.id}`")
                meta_str = " — " + ", ".join(meta) if meta else ""
                lines.append(f"- **{entry.title}**{meta_str}")
            lines.append("")
            lines.append("## Other Jarvis Threads")
            lines.append("")

        for entry in entries:
            meta = []
            if entry.created_at:
                meta.append(f"created: `{entry.created_at}`")
            if entry.id:
                meta.append(f"id: `{entry.id}`")
            meta_str = " — " + ", ".join(meta) if meta else ""
            prefix = "⭐ " if entry.is_core else "- "
            lines.append(f"{prefix}**{entry.title}**{meta_str}")

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_user_snapshot(user_data: Any) -> None:
    """Write a raw snapshot of user export metadata."""
    target = JARVIS_DIR / "user-export-snapshot.md"
    lines = [
        "# User Export Snapshot",
        "",
        "Raw `user.json` data from GPT export (redacted/edited manually as needed).",
        "",
        "```json",
        json.dumps(user_data, indent=2, ensure_ascii=False),
        "```",
        "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    JARVIS_DIR.mkdir(parents=True, exist_ok=True)

    conversations = load_json(EXPORT_DIR / "conversations.json")
    entries = index_jarvis_conversations(conversations)
    write_conversation_index(entries)

    user_data = load_json(EXPORT_DIR / "user.json")
    if user_data is not None:
        write_user_snapshot(user_data)

    print("Jarvis docs refreshed from GPT export under docs/gpt export/")


if __name__ == "__main__":
    main()
