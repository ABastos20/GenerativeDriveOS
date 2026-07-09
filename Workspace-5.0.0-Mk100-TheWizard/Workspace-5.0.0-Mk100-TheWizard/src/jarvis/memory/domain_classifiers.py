"""Domain classification helpers for heuristic metadata extraction.

Extracted from _heuristic_metadata_from_payload to reduce its LOC.
"""
from typing import Optional, List

# Import domain maps
from jarvis.memory.domain_heuristics import CHAVAO_DOMAIN_MAP, DIRECT_DOMAIN_MAP, GD_KEYWORD_TAGS


def classify_by_path(source_file: str) -> tuple[Optional[str], List[str]]:
    """Classify domain by source file path.
    
    Returns:
        (primary_domain, tags)
    """
    lowered_path = source_file.replace("\\", "/").lower()
    primary: Optional[str] = None
    tags: List[str] = []

    # GenerativeDrive playbooks - match BEFORE generic jarvis.playbooks
    if "docs/jarvis/" in lowered_path and "gd-" in lowered_path:
        if "gd-overview" in lowered_path:
            primary = "gd.generativedrive"
        elif "gd-energy-partnerships" in lowered_path or "gd-partnerships" in lowered_path:
            primary = "gd.partnerships"
        elif "gd-hydrogen" in lowered_path:
            primary = "gd.hydrogen"
        elif "gd-telemetry" in lowered_path or "gd-infra" in lowered_path:
            primary = "gd.infra"
        else:
            primary = "gd.generativedrive"
        tags.extend(["generative_drive"])

    # Jarvis docs and playbooks
    if not primary and "docs/jarvis/" in lowered_path:
        if "playbooks/" in lowered_path:
            primary = "jarvis.playbooks"
        else:
            primary = "jarvis.core"

    # Sprint docs
    if "docs/sprints/" in lowered_path:
        primary = primary or "project.sprints"

    # BMAD assets
    if "/.bmad/bmm/" in lowered_path or "/bmad/bmm/" in lowered_path:
        primary = primary or "bmad.method"
    elif "/.bmad/core/" in lowered_path or "/bmad/core/" in lowered_path:
        primary = primary or "bmad.core"

    # CGD proposals
    if "/docs/cgd/" in lowered_path:
        primary = primary or "cgd.brain"

    # GPT export
    if "docs/gptexportnew/" in lowered_path:
        primary = primary or "jarvis.gpt_export"

    # OneDrive paths
    if "CyberSecurityPortfolio" in source_file:
        primary = "cyber.security"
        tags.extend(["cyber_security", "network_security"])
    elif "GenerativeDrive" in source_file or "GDFullDocument" in source_file:
        primary = "gd.generativedrive"
        tags.extend(["generative_drive", "energy_model"])

    return primary, tags


def classify_by_title(title: str) -> tuple[Optional[str], List[str]]:
    """Classify domain by document title.
    
    Returns:
        (primary_domain, tags)
    """
    lowered = title.lower()
    primary: Optional[str] = None
    tags: List[str] = []

    if "generativedrive" in lowered or "generative drive" in lowered or " gd " in lowered:
        primary = "gd.generativedrive"
        tags.append("generative_drive")
        if "sines" in lowered:
            tags.append("sines")
        if "hydrogen" in lowered or "hidrog" in lowered:
            tags.append("hydrogen")
    elif "bm ad" in lowered or "bmad" in lowered:
        primary = "bmad.method"
    elif "retrospective" in lowered or "retro" in lowered:
        primary = "project.retrospective"
    elif "epic " in lowered:
        primary = "project.epic"
    elif "story " in lowered:
        primary = "project.story"

    return primary, tags


def classify_by_section(section: str) -> Optional[str]:
    """Classify domain by section name.
    
    Returns:
        primary_domain
    """
    lowered_section = section.lower()
    
    if "architecture" in lowered_section:
        return "architecture.core"
    elif "prd" in lowered_section or "product requirements" in lowered_section:
        return "product.prd"
    elif "test-design" in lowered_section or "test design" in lowered_section:
        return "quality.tests"
    
    return None


def classify_by_text_content(
    source_file: str,
    section: str,
    title: str,
    text: str,
    current_primary: Optional[str],
) -> tuple[Optional[str], List[str]]:
    """Classify domain by text content analysis.
    
    Returns:
        (primary_domain, additional_tags)
    """
    text_snippet = (text or "")[:2000]
    combined = " ".join([source_file, section, title, text_snippet]).lower()
    
    primary = current_primary
    tags: List[str] = []

    # Generative Drive detection
    if "generativedrive" in combined or "generative drive" in combined or "gd sines" in combined:
        if not primary:
            primary = "gd.generativedrive"
        if "generative_drive" not in tags:
            tags.append("generative_drive")
        
        # Add topical tags
        for needle, tag in GD_KEYWORD_TAGS.items():
            if needle in combined and tag not in tags:
                tags.append(tag)

        # Sines + hydrogen heuristic
        if primary != "gd.generativedrive":
            has_sines = "sines" in combined
            has_h2 = any(
                token in combined
                for token in ("hydrogen", "hidrog", "hidrogénio", "hidrogenio", "hidrogênio", " h2 ")
            )
            if has_sines and has_h2:
                primary = "gd.generativedrive"
                if "generative_drive" not in tags:
                    tags.append("generative_drive")
                if "sines" not in tags:
                    tags.append("sines")
                if "hydrogen" not in tags:
                    tags.append("hydrogen")

    # Generic buzzword domains
    if not primary:
        for needle, dom_key in CHAVAO_DOMAIN_MAP.items():
            if needle in combined:
                primary = dom_key
                tag_key = dom_key.replace(".", "_")
                if tag_key not in tags:
                    tags.append(tag_key)
                break

    return primary, tags


def get_extension_default(source_file: str) -> Optional[str]:
    """Get default domain based on file extension.
    
    Returns:
        doc_type_hint
    """
    if source_file.endswith(".pdf"):
        return "docs.pdf"
    elif source_file.endswith(".md") or source_file.endswith(".markdown"):
        return "docs.markdown"
    elif source_file.endswith(".txt"):
        return "docs.text"
    return None


def classify_from_ingestion_policy(path_obj) -> tuple[str, List[str], dict]:
    """
    Classify a doc under docs/ into (domain, tags, meta) per dataSetRules.md.
    Refactored from ingest_workspace_docs.py.
    
    meta MUST include:
      - is_latest: bool
      - is_system: bool
      - jarvis_core: bool
      - priority: float (0.0-1.0)
      - semantic_family: str
    """
    # Defensive import to avoid circular dependency issues at top level if any
    from datetime import datetime
    
    # Normalize path to relative if possible, or use parts
    # Assuming path_obj is a Path object
    parts = path_obj.parts
    name = path_obj.name
    lower = name.lower()
    stem = path_obj.stem
    
    # Check for workspace/docs prefix if present
    # This logic assumes we are looking at the path relative to 'docs' if possible
    # We'll try to find 'docs' in parts and slice from there
    try:
        docs_idx = parts.index('docs')
        if len(parts) > docs_idx + 1:
            parts = parts[docs_idx + 1:]
        else:
            # path is .../docs/filename
            pass
    except ValueError:
        pass

    domain = "docs"
    tags: List[str] = []
    meta: dict = {
        "is_latest": True,
        "is_system": False,
        "jarvis_core": False,
        "priority": 0.5,
        "semantic_family": "docs",
    }
    
    # Helper to parse date
    def _parse_date(fname: str):
        # YYYY-MM-DD pattern
        # Simple extraction
        import re
        m = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
        if m:
            try:
                return datetime.fromisoformat(m.group(1))
            except ValueError:
                return None
        return None

    # 4.1 architecture (docs/architecture/* and docs/architecture.md)
    if (len(parts) > 0 and parts[0] == "architecture") or name == "architecture.md":
        domain = "jarvis.architecture"
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

    # 4.2 archive (docs/archive/*) - STALE
    elif len(parts) > 0 and parts[0] == "archive":
        domain = "jarvis.core"
        tags += ["archive", "legacy", "historical", "old_blueprint"]
        meta["semantic_family"] = "archive"
        meta["is_latest"] = False
        meta["priority"] = 0.2
        meta["stale_factor"] = 1.0

    # 4.3 features (docs/features/*)
    elif len(parts) > 0 and parts[0] == "features":
        domain = "jarvis.architecture"
        tags += ["features", "ui", "jarvis"]
        meta["semantic_family"] = "feature"
        meta["priority"] = 0.75
        
        if name == "advanced-conversation-management.md":
            tags += ["conversation_management"]
        elif name == "conversation-pagination-search.md":
            tags += ["pagination", "search"]
        elif name == "ui-collapsible-panels.md":
            tags += ["panels", "research_ui"]

    # 4.4 jarvis-core (docs/jarvis/*)
    elif len(parts) > 0 and parts[0] == "jarvis":
        if len(parts) >= 2 and parts[1] == "playbooks":
            # jarvis-playbooks
            domain = "jarvis.playbooks"
            tags += ["jarvis", "playbook"]
            meta["semantic_family"] = "playbook"
            meta["priority"] = 0.8
            meta["jarvis_core"] = False
            meta["is_system"] = False
        else:
            # ═══ SYSTEM BRAIN ═══
            domain = "jarvis.core"
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

    # 4.6 sessions (docs/sessions/*)
    elif len(parts) > 0 and parts[0] == "sessions":
        domain = "jarvis.conversations"
        tags += ["session_log", "temporal", "jarvis_session"]
        meta["semantic_family"] = "session-log"
        meta["priority"] = 0.5
        
        sd = _parse_date(name)
        if sd:
            meta["session_date"] = sd.isoformat()
        
        up = name.upper()
        if "BREAKTHROUGH" in up:
            tags.append("breakthrough")
        if "COUNCIL" in up:
            tags.append("council")
        if "DOC-VIEWER" in up or "DOC_VIEWER" in up:
            tags.append("doc_viewer")
        if "DOMAIN-FILTERING" in up:
            tags.append("domain_filtering")
        if "BRAINSTORM" in up:
            tags.append("brainstorming")

    # 4.7 story / epic / process (docs/sprints/*)
    elif len(parts) > 0 and parts[0] == "sprints":
        if len(parts) >= 2 and parts[1] == "stories":
            # BMAD stories
            domain = "project.story"
            tags += ["story", "bmad"]
            meta["semantic_family"] = "story"
            meta["priority"] = 0.6
            
            if name[0].isdigit():
                epic_prefix = name.split("-", 2)[0]
                tags.append(f"epic_{epic_prefix}")
            
            sd = _parse_date(name)
            if sd:
                meta["story_date"] = sd.isoformat()
            
            if name.endswith(".context.xml"):
                meta["semantic_family"] = "story-context"
                tags += ["story_context", "xml"]
                meta["priority"] = 0.4
            
            if name.startswith("4-5-"):
                tags += ["epic_4_5", "arches"]
            if name.startswith("4-8-"):
                tags += ["epic_4_8", "autonomous_research", "gap_detection"]
            if name.startswith("4-9-"):
                tags.append("epic_4_9")
        else:
            # epics, retros, status
            if lower.startswith("epic-"):
                domain = "project.epic"
                tags += ["epic", "bmad"]
                meta["semantic_family"] = "epic"
                meta["priority"] = 0.7
                if "retro" in lower:
                    tags.append("retrospective")
                if "arches-stabilization" in lower:
                    tags.append("arches")
                if "epic-5-prep-plan" in lower:
                    tags += ["epic_5", "cost_optimization"]
            elif lower == "sprint-status.yaml":
                domain = "project.sprints"
                tags += ["sprint_status", "bmad", "process"]
                meta["semantic_family"] = "process"
                meta["priority"] = 0.6
            else:
                domain = "project.sprints"
                tags += ["bmad", "process"]
                meta["semantic_family"] = "process"
                meta["priority"] = 0.5

    # 4.9 root docs
    elif len(parts) > 0 and parts[0] == "datasetRules":
        domain = "jarvis.core"
        tags += ["dataset_rules", "ingestion", "ontology"]
        meta["semantic_family"] = "docs"
        meta["priority"] = 0.8
    else:
        # misc heuristics for root docs
        if name == "jarvis-knowledge-pipeline.md":
            domain = "jarvis.architecture"
            tags += ["knowledge_pipeline", "memory"]
            meta["semantic_family"] = "architecture"
            meta["priority"] = 0.9
        elif name.startswith("LLM_"):
            domain = "jarvis.llm"
            tags += ["llm", "models"]
            meta["semantic_family"] = "llm"
            meta["priority"] = 0.6
        elif lower.startswith("autonomous-research"):
            domain = "jarvis.agents"
            tags += ["autonomous_research", "research"]
            meta["semantic_family"] = "feature"
            meta["priority"] = 0.7
        elif lower.startswith("variable-grounding-system"):
            domain = "jarvis.architecture"
            tags += ["variable_grounding"]
            meta["semantic_family"] = "feature"
            meta["priority"] = 0.7
        elif lower.startswith("bugfixes"):
            domain = "jarvis.core"
            tags += ["bugfix"]
            meta["semantic_family"] = "troubleshooting"
            meta["priority"] = 0.5
        elif lower.startswith("troubleshooting"):
            domain = "jarvis.core"
            tags += ["troubleshooting"]
            meta["semantic_family"] = "troubleshooting"
            meta["priority"] = 0.5
        elif lower in ("readme.md", "quick-reference.md", "enhancements-quick-start.md"):
            domain = "jarvis.core"
            tags += ["readme", "quick_start"]
            meta["semantic_family"] = "docs"
            meta["priority"] = 0.7
        elif "brain-status" in lower:
            domain = "project.sprints"
            tags += ["brain_status", "snapshot"]
            meta["semantic_family"] = "status"
            meta["priority"] = 0.6
        elif "integration" in lower:
            domain = "project.sprints"
            tags += ["integration_status"]
            meta["semantic_family"] = "status"
            meta["priority"] = 0.6
        elif name == "epics.md":
            domain = "project.epic"
            tags += ["epic_index", "overview"]
            meta["semantic_family"] = "epic"
            meta["priority"] = 0.7
        elif name == "prd.md":
            domain = "product.prd"
            tags += ["prd", "requirements"]
            meta["semantic_family"] = "planning"
            meta["priority"] = 0.75
        elif "agent" in lower:
            domain = "jarvis.agents"
            tags += ["agents", "coordination"]
            meta["semantic_family"] = "agents"
            meta["priority"] = 0.7
        else:
            domain = "jarvis.core"
            tags += ["docs"]
            meta["semantic_family"] = "docs"

    # Automatic stem tag
    base_tag = stem.replace(".", "_").replace(" ", "_").replace("-", "_").lower()
    if base_tag and len(base_tag) <= 50:
        tags.append(base_tag)
    
    tags = sorted(set(tags))
    return domain, tags, meta
