#!/usr/bin/env python
"""
Discovery + heuristic ingestion using Jarvis domain heuristics.

Scans configured roots, extracts lightweight text previews, applies
CHAVAO_DOMAIN_MAP / path hints, and (optionally) ingests files into memory.

Usage:
    python scripts/discover_and_ingest.py --manifest /workspace/ingest_manifest.json
    python scripts/discover_and_ingest.py --ingest

Notes:
- Extraction for PDFs/docx is best-effort; if pypdf/python-docx are missing,
  the script will skip text extraction for those files and fall back to path hints.
- A state file (.ingest_state.json) prevents re-processing unchanged files by hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from jarvis.memory.domain_heuristics import CHAVAO_DOMAIN_MAP

ROOTS_DEFAULT = [Path("/mnt/OneDrive"), Path("/workspace")]
EXTS_DEFAULT = {".pdf", ".md", ".txt", ".docx"}
STATE_FILE = Path("/workspace/.ingest_state.json")


def load_state() -> Dict[str, dict]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_state(state: Dict[str, dict]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def extract_text(path: Path, max_chars: int = 12000) -> str:
    """Best-effort text extraction."""
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        try:
            return path.read_text(errors="ignore")[:max_chars]
        except Exception:
            return ""
    if suffix == ".pdf":
        try:
            import pypdf  # type: ignore
        except Exception:
            return ""
        try:
            reader = pypdf.PdfReader(str(path))
            chunks: List[str] = []
            for page in reader.pages[:8]:
                page_text = page.extract_text() or ""
                if page_text:
                    chunks.append(page_text)
            return "\n".join(chunks)[:max_chars]
        except Exception:
            return ""
    if suffix == ".docx":
        try:
            import docx  # type: ignore
        except Exception:
            return ""
        try:
            document = docx.Document(str(path))
            return "\n".join(p.text for p in document.paragraphs)[:max_chars]
        except Exception:
            return ""
    return ""


def path_domain_hint(path: Path) -> Optional[str]:
    lower = str(path).lower()
    if "generative-drive" in lower or "/gd/" in lower:
        return "gd.generative_drive"
    if "docs/jarvis" in lower:
        return "jarvis.core"
    if "docs/sprints" in lower:
        return "jarvis.sprints"
    if "conversation" in lower or "chat" in lower:
        return "jarvis.conversations"
    if "executive" in lower or "summary" in lower or "board" in lower:
        return "jarvis.executive"
    if "plan" in lower or "strategy" in lower:
        return "jarvis.strategy"
    return None


def content_domain(text: str) -> Optional[str]:
    lower = text.lower()
    scores: Dict[str, int] = {}
    for keyword, domain in CHAVAO_DOMAIN_MAP.items():
        if keyword in lower:
            scores[domain] = scores.get(domain, 0) + 1
    if not scores:
        return None
    # Pick the domain with max hits; tie-breaker is lexicographic.
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def extract_summary_points(text: str, max_points: int = 8) -> Tuple[List[str], List[str]]:
    """Heuristically extract summary/conclusion points."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    triggers = ("summary", "conclusion", "key takeaways", "tl;dr", "findings")
    points: List[str] = []
    tags: List[str] = []

    def looks_like_bullet(s: str) -> bool:
        return (
            s[:2].isdigit()
            or s.startswith(("-", "*"))
            or s[:3].lower() in {"1)", "2)", "3)", "i)", "ii)", "iii)"}
        )

    # Look for explicit trigger headings first
    for idx, line in enumerate(lines):
        lower = line.lower()
        if any(t in lower for t in triggers):
            for nxt in lines[idx + 1 : idx + 1 + 14]:
                if looks_like_bullet(nxt) or len(nxt.split()) <= 12:
                    points.append(nxt)
            if points:
                tags.append("has_summary")
                if any(looks_like_bullet(p) for p in points):
                    tags.append("numbered_summary")
            break

    # Fallback: first bulleted/numbered list anywhere
    if not points:
        for line in lines:
            if looks_like_bullet(line):
                points.append(line)
        if points:
            tags.append("numbered_summary")

    return points[:max_points], tags


def classify(path: Path, text: str, summary_text: str = "") -> str:
    # 1) Path hints
    hinted = path_domain_hint(path)
    if hinted:
        return hinted
    sample = summary_text or text
    # 2) Content heuristics
    domain = content_domain(sample)
    if domain:
        return domain
    # 3) Fallback
    return "jarvis.docs"


def ingest_file(path: Path, domain: str, collection: str = "knowledge") -> None:
    cmd = [
        "poetry",
        "run",
        "jarvis",
        "memory",
        "add",
        str(path),
        "--collection",
        collection,
        "--source",
        domain,
    ]
    subprocess.run(cmd, cwd="/workspace", check=False)


def discover(
    roots: List[Path],
    exts: set[str],
    ingest: bool,
    collection: str,
    manifest_path: Path,
) -> List[dict]:
    state = load_state()
    new_state: Dict[str, dict] = {}
    manifest: List[dict] = []

    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in exts:
                continue
            if not path.is_file():
                continue
            size = path.stat().st_size
            if size > 300 * 1024 * 1024:  # Skip very large files
                continue
            text = extract_text(path)
            h = sha1_text(text) if text else ""
            key = str(path)

            prev = state.get(key)
            if prev and prev.get("hash") == h:
                new_state[key] = prev
                continue

            summary_points, summary_tags = extract_summary_points(text)
            summary_excerpt = "\n".join(summary_points)
            domain = classify(path, text, summary_text=summary_excerpt)
            entry = {
                "path": key,
                "domain": domain,
                "hash": h,
                "size": size,
                "ingested": False,
                "summary_excerpt": summary_excerpt,
                "summary_tags": summary_tags,
            }

            if ingest:
                ingest_file(path, domain, collection=collection)
                entry["ingested"] = True

            manifest.append(entry)
            new_state[key] = entry

    save_state(new_state)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Discover and optionally ingest files using domain heuristics.")
    ap.add_argument("--ingest", action="store_true", help="Ingest discovered files into Jarvis memory.")
    ap.add_argument(
        "--manifest",
        type=Path,
        default=Path("/workspace/ingest_manifest.json"),
        help="Path to write discovery manifest JSON.",
    )
    ap.add_argument(
        "--collection",
        type=str,
        default="knowledge",
        help="Qdrant collection name for ingestion.",
    )
    ap.add_argument(
        "--roots",
        type=str,
        nargs="*",
        default=[str(p) for p in ROOTS_DEFAULT],
        help="Root paths to scan (space-separated).",
    )
    ap.add_argument(
        "--ext",
        type=str,
        nargs="*",
        default=list(EXTS_DEFAULT),
        help="File extensions to include.",
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    roots = [Path(p) for p in args.roots]
    exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.ext}

    manifest = discover(
        roots=roots,
        exts=exts,
        ingest=args.ingest,
        collection=args.collection,
        manifest_path=args.manifest,
    )
    sys.stdout.write(json.dumps({"count": len(manifest), "manifest": str(args.manifest)}, indent=2) + "\n")


if __name__ == "__main__":
    main()
