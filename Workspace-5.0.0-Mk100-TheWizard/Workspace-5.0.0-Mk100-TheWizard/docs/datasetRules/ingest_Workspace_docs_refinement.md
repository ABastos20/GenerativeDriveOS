Perfect, let’s hard-wire the rules into code.
Below is an updated classify() + script that matches exactly what we wrote in dataSetRules.md. You can drop this as scripts/ingest_workspace_docs.py (or merge into your existing one) and then just wire ingest_file() into your real pipeline.
#!/usr/bin/env python
import pathlib
from datetime import datetime
from typing import Dict, List, Tuple

# Adjust BASE if inside container (e.g. pathlib.Path("/app/Workspace/docs"))
BASE = pathlib.Path("Workspace/docs").resolve()


def classify(path: pathlib.Path) -> Tuple[str, List[str], Dict]:
    """
    Classify a doc under Workspace/docs into (domain, tags, meta) according to docs/dataSetRules.md.

    meta MUST include at least:
      - is_latest: bool
      - is_system: bool
      - jarvis_core: bool
      - priority: float
      - semantic_family: str
    Versioning (version, is_latest flipping) is handled by the ingest pipeline, not here.
    """
    rel = path.relative_to(BASE)
    parts = rel.parts

    domain = "docs"
    tags: List[str] = []
    meta: Dict = {
        "is_latest": True,
        "is_system": False,
        "jarvis_core": False,
        "priority": 0.5,
        "semantic_family": "docs",
    }

    name = rel.name
    lower = name.lower()
    stem = rel.stem

    # -------------------------------------------------------------------------
    # 4.1 architecture  (docs/architecture/* and docs/architecture.md)
    # -------------------------------------------------------------------------
    if parts[0] == "architecture" or name == "architecture.md":
        domain = "architecture"
        tags += ["architecture", "jarvis", "design", "memory"]
        meta["semantic_family"] = "architecture"
        meta["priority"] = 0.9

        if name == "jarvis-memory-architecture.md":
            tags += ["memory_core", "arches"]
        elif name == "memory-pipeline-flow.md":
            tags += ["pipeline_flow"]
        elif name == "domain-taxonomy.md":
            tags += ["domain_taxonomy"]
        elif name == "jarvis-knowledge-pipeline.md":
            tags += ["knowledge_pipeline", "memory"]

    # -------------------------------------------------------------------------
    # 4.2 archive  (docs/archive/*)
    # -------------------------------------------------------------------------
    elif parts[0] == "archive":
        domain = "archive"
        tags += ["archive", "legacy", "historical", "old_blueprint"]
        meta["semantic_family"] = "archive"
        meta["is_latest"] = False
        meta["priority"] = 0.2
        meta["stale_factor"] = 1.0

    # -------------------------------------------------------------------------
    # 4.3 features  (docs/features/* and some root feature docs)
    # -------------------------------------------------------------------------
    elif parts[0] == "features":
        domain = "features"
        tags += ["features", "ui", "jarvis"]
        meta["semantic_family"] = "feature"
        meta["priority"] = 0.75

        if name == "advanced-conversation-management.md":
            tags += ["conversation_management"]
        elif name == "conversation-pagination-search.md":
            tags += ["pagination", "search"]
        elif name == "ui-collapsible-panels.md":
            tags += ["panels", "research_ui"]

    # -------------------------------------------------------------------------
    # 4.4 jarvis-core  (docs/jarvis/* excluding playbooks)
    # 4.5 jarvis-playbooks (docs/jarvis/playbooks/*)
    # -------------------------------------------------------------------------
    elif parts[0] == "jarvis":
        if len(parts) >= 2 and parts[1] == "playbooks":
            # jarvis-playbooks
            domain = "jarvis-playbooks"
            tags += ["jarvis", "playbook"]
            meta["semantic_family"] = "playbook"
            meta["priority"] = 0.8
            meta["jarvis_core"] = False
            meta["is_system"] = False
        else:
            # jarvis-core (SYSTEM BRAIN)
            domain = "jarvis-core"
            tags += ["jarvis", "core", "arches", "cognition", "memory"]
            meta["semantic_family"] = "core-memory"
            meta["priority"] = 1.0
            meta["jarvis_core"] = True
            meta["is_system"] = True

            # per-file tags
            if name == "memory.core.md":
                tags += ["memory_core", "ontology", "priority_high"]
            elif name == "operating-manual.md":
                tags += ["operating_manual", "ops"]
            elif name == "persona.md":
                tags += ["personas", "council"]
            elif name == "gd-overview.md":
                tags += ["generative_drive", "gd_core"]
            elif name == "integration-plan.md":
                tags += ["integration", "roadmap"]
            elif name == "conversation-index.md":
                tags += ["conversation_index"]
            elif name == "user-export-snapshot.md":
                tags += ["user_export_snapshot"]

    # -------------------------------------------------------------------------
    # 4.6 sessions  (docs/sessions/*)
    # -------------------------------------------------------------------------
    elif parts[0] == "sessions":
        domain = "sessions"
        tags += ["session_log", "temporal", "jarvis_session"]
        meta["semantic_family"] = "session-log"
        meta["priority"] = 0.5

        # parse date from filename prefix YYYY-MM-DD-*
        try:
            # e.g. 2025-12-03-BREAKTHROUGH-SESSION.md
            date_prefix = "-".join(name.split("-", 3)[:3])
            dt = datetime.strptime(date_prefix, "%Y-%m-%d")
            meta["session_date"] = dt.isoformat()
        except Exception:
            pass

        # high level tags from name
        up = name.upper()
        if "BREAKTHROUGH" in up:
            tags.append("breakthrough")
        if "COUNCIL" in up:
            tags.append("council")
        if "DOC-VIEWER" in up or "DOC_VIEWER" in up:
            tags.append("doc_viewer")
        if "DOMAIN-FILTERING" in up:
            tags.append("domain_filtering")

    # -------------------------------------------------------------------------
    # 4.7 story  (docs/sprints/stories/*)
    # 4.8 epic / process  (other docs/sprints/*)
    # -------------------------------------------------------------------------
    elif parts[0] == "sprints":
        # stories (BMAD)
        if len(parts) >= 2 and parts[1] == "stories":
            domain = "story"
            tags += ["story", "bmad"]
            meta["semantic_family"] = "story"
            meta["priority"] = 0.6

            filename_no_ext = name
            if filename_no_ext[0].isdigit():
                epic_prefix = filename_no_ext.split("-", 2)[0]
                tags.append(f"epic_{epic_prefix}")

            # distinguish context XML
            if name.endswith(".context.xml"):
                meta["semantic_family"] = "story-context"
                tags += ["story_context", "xml"]
                meta["priority"] = 0.4

            # specific epic tags
            if name.startswith("4-5-"):
                tags.append("epic_4_5")
                tags.append("arches")
            if name.startswith("4-8-"):
                tags.append("epic_4_8")
                tags += ["autonomous_research", "gap_detection"]
        else:
            # epics, retros, status, etc
            lower_name = lower
            if lower_name.startswith("epic-"):
                domain = "epic"
                tags += ["epic", "bmad"]
                meta["semantic_family"] = "epic"
                meta["priority"] = 0.7

                if "retro" in lower_name:
                    tags.append("retrospective")
                if "arches-stabilization" in lower_name:
                    tags.append("arches")
                if "epic-5-prep-plan" in lower_name:
                    tags += ["epic_5", "cost_optimization"]
            elif lower_name == "sprint-status.yaml":
                domain = "process"
                tags += ["sprint_status", "bmad", "process"]
                meta["semantic_family"] = "process"
                meta["priority"] = 0.6
            else:
                domain = "process"
                tags += ["bmad", "process"]
                meta["semantic_family"] = "process"
                meta["priority"] = 0.5

    # -------------------------------------------------------------------------
    # 4.9 root docs and everything else (docs/*.md, etc.)
    # -------------------------------------------------------------------------
    else:
        # root-level / misc docs
        if name == "architecture.md":
            domain = "architecture"
            tags += ["architecture", "overview", "jarvis_architecture"]
            meta["semantic_family"] = "architecture"
            meta["priority"] = 0.9
        elif name == "jarvis-knowledge-pipeline.md":
            domain = "architecture"
            tags += ["knowledge_pipeline", "memory"]
            meta["semantic_family"] = "architecture"
            meta["priority"] = 0.9
        elif name.startswith("LLM_"):
            domain = "llm"
            tags += ["llm", "models"]
            meta["semantic_family"] = "llm"
            meta["priority"] = 0.6
        elif lower.startswith("autonomous-research"):
            domain = "features"
            tags += ["autonomous_research", "research"]
            meta["semantic_family"] = "feature"
            meta["priority"] = 0.7
        elif lower.startswith("variable-grounding-system"):
            domain = "features"
            tags += ["variable_grounding"]
            meta["semantic_family"] = "feature"
            meta["priority"] = 0.7
        elif lower.startswith("bugfixes"):
            domain = "troubleshooting"
            tags += ["bugfix"]
            meta["semantic_family"] = "troubleshooting"
            meta["priority"] = 0.5
        elif lower.startswith("troubleshooting"):
            domain = "troubleshooting"
            tags += ["troubleshooting"]
            meta["semantic_family"] = "troubleshooting"
            meta["priority"] = 0.5
        elif lower in ("readme.md", "quick-reference.md", "enhancements-quick-start.md"):
            domain = "docs"
            tags += ["readme", "quick_start"]
            meta["semantic_family"] = "docs"
            meta["priority"] = 0.7
        else:
            domain = "docs"
            tags += ["docs"]
            meta["semantic_family"] = "docs"
            meta["priority"] = meta.get("priority", 0.5)

    # -------------------------------------------------------------------------
    # Automatic filename-based tag (always)
    # -------------------------------------------------------------------------
    base_tag = stem.replace(".", "_").replace(" ", "_").lower()
    tags.append(base_tag)

    # De-duplicate + sort
    tags = sorted(set(tags))

    return domain, tags, meta


def iter_files():
    for path in BASE.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".xml", ".yaml", ".yml"}:
            yield path


def ingest_file(path: pathlib.Path, domain: str, tags: List[str], meta: Dict):
    """
    PLACEHOLDER: wire this into your actual ingest pipeline.

    Typical integration:
      - Call Python ingest:
          from jarvis.memory.ingest import ingest_file as jarvis_ingest
          jarvis_ingest(path, domain=domain, tags=tags, meta=meta)
      - Or shell out to your existing CLI ingest script.
    """
    print(f"[DRY-RUN] {path} -> domain={domain}, tags={tags}, meta={meta}")
    # TODO: replace this print with real ingestion call


def main(dry_run: bool = True):
    for path in iter_files():
        domain, tags, meta = classify(path)
        if dry_run:
            ingest_file(path, domain, tags, meta)
        else:
            # here you call your real ingest without the [DRY-RUN] label
            ingest_file(path, domain, tags, meta)


if __name__ == "__main__":
    # First run in dry-run mode, then set dry_run=False when happy.
    main(dry_run=True)

How to use
Inside the container (or host, depending on where Jarvis runs):
cd /app/Workspace   # or wherever your Workspace root is
python scripts/ingest_workspace_docs.py  # dry run, just prints

Inspect a few key lines for:


docs/jarvis/memory.core.md → domain=jarvis-core, is_system=True, jarvis_core=True, semantic_family=core-memory, priority=1.0.


docs/archive/prd-original.md → domain=archive, is_latest=False, stale_factor=1.0, low priority.


docs/sprints/stories/4-5-6-cognitive-trace-log.md → domain=story, tags includes ["story", "bmad", "epic_4", "epic_4_5", "arches", ...].


When you’re happy, flip main(dry_run=False) or pass a flag if you prefer, and wire ingest_file() to your actual ingestion call.
This gives you exactly what you asked: Vision-grade classification, not Ultron — system plane separated, core flagged, and everything ready for ARCHES to sit on top cleanly.
