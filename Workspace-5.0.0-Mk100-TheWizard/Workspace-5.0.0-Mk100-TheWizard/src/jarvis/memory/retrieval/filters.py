from __future__ import annotations

import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple, Union

import structlog
from qdrant_client import models as qmodels

from jarvis.memory.domain_heuristics import CHAVAO_DOMAIN_MAP
from jarvis.memory.retrieval.types import RetrievalMode, SearchResult

logger = structlog.get_logger(__name__)

# Freshness scoring constants
FRESHNESS_HALFLIFE_DAYS = 30
DEFAULT_MIN_FRESHNESS = 0.5

MONTH_NAMES = {
    "jan": 1, "january": 1, "janeiro": 1, "janvier": 1,
    "feb": 2, "february": 2, "fevereiro": 2, "février": 2,
    "mar": 3, "march": 3, "março": 3, "mars": 3,
    "apr": 4, "april": 4, "abril": 4, "avril": 4,
    "may": 5, "maio": 5, "mai": 5,
    "jun": 6, "june": 6, "junho": 6, "juin": 6,
    "jul": 7, "july": 7, "julho": 7, "juillet": 7,
    "aug": 8, "august": 8, "agosto": 8, "août": 8,
    "sep": 9, "sept": 9, "september": 9, "setembro": 9, "septembre": 9,
    "oct": 10, "october": 10, "outubro": 10, "octobre": 10,
    "nov": 11, "november": 11, "novembro": 11, "novembre": 11,
    "dec": 12, "december": 12, "dezembro": 12, "décembre": 12,
}

def _parse_month_name(name: str) -> Optional[int]:
    return MONTH_NAMES.get(name.lower().strip())

DATE_PATTERNS = [
    (r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
    (r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", lambda m: (int(m.group(3)), int(m.group(1)), int(m.group(2)))),
    (r"([A-Za-z]+)\s+(\d{1,2})(?:,?\s+|\s+)(\d{4})", lambda m: (int(m.group(3)), _parse_month_name(m.group(1)) or 0, int(m.group(2)))),
    (r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", lambda m: (int(m.group(3)), _parse_month_name(m.group(2)) or 0, int(m.group(1)))),
]

META_KEYWORDS = frozenset([
    "jarvis", "memory.core", "operating manual", "how do you work",
    "your architecture", "your memory", "cognitive", "council of ricks",
    "arches controller", "jarvis-core", "system plane", "explain yourself",
    "summarise memory", "summarize memory", "your brain", "your design",
])

TEMPORAL_KEYWORDS = frozenset([
    "on that day", "that week", "that month", "what happened",
    "what did i do", "session on", "meeting on", "decisions on",
    "between", "from", "to", "during",
])

HISTORICAL_KEYWORDS = frozenset([
    "original prd", "before epic", "old version", "first plan",
    "legacy", "historical", "archive", "old blueprint",
])

def parse_date_from_query(query: str) -> Optional[datetime]:
    for pattern, extractor in DATE_PATTERNS:
        match = re.search(pattern, query)
        if match:
            try:
                year, month, day = extractor(match)
                return datetime(year, month, day, tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue
    return None

def detect_retrieval_mode(query: str) -> Tuple[RetrievalMode, Optional[datetime]]:
    query_lower = query.lower()
    date = parse_date_from_query(query)
    
    if date or any(kw in query_lower for kw in TEMPORAL_KEYWORDS):
        if date:
            return RetrievalMode.TIME_SLICE, date
    
    if any(kw in query_lower for kw in META_KEYWORDS):
        return RetrievalMode.META, None
    
    if any(kw in query_lower for kw in HISTORICAL_KEYWORDS):
        return RetrievalMode.HISTORICAL, None
    
    return RetrievalMode.NORMAL, None

def _compute_freshness_score(result: SearchResult) -> float:
    payload = result.metadata or {}
    timestamp = (
        payload.get("doc_last_seen") 
        or payload.get("ingested_at") 
        or payload.get("created_at")
    )
    
    if not timestamp:
        return 1.0
    
    try:
        if isinstance(timestamp, str):
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif isinstance(timestamp, (int, float)):
            ts = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        elif isinstance(timestamp, datetime):
            ts = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
        else:
            return 1.0
    except (ValueError, TypeError):
        return 1.0
    
    now = datetime.now(timezone.utc)
    age_days = max(0, (now - ts).total_seconds() / 86400)
    freshness = 1.0 / (1 + age_days / FRESHNESS_HALFLIFE_DAYS)
    return round(freshness, 4)

def apply_freshness_filter(
    results: List[SearchResult],
    min_freshness: float = DEFAULT_MIN_FRESHNESS,
    allow_stale: bool = False,
) -> List[SearchResult]:
    if not results:
        return results
    
    for result in results:
        result.freshness_score = _compute_freshness_score(result)
    
    if allow_stale:
        stale_count = sum(1 for r in results if r.freshness_score < min_freshness)
        if stale_count > 0:
            logger.warning("stale_documents_included", stale_count=stale_count)
        return results
    
    fresh_results = [r for r in results if r.freshness_score >= min_freshness]
    
    if len(fresh_results) < len(results):
        logger.info(
            "freshness_filter_applied",
            original_count=len(results),
            fresh_count=len(fresh_results),
            threshold=min_freshness,
        )
    
    return fresh_results

def resolve_version_conflicts(results: List[SearchResult]) -> List[SearchResult]:
    if not results:
        return results
    
    families: Dict[str, Dict[str, List[SearchResult]]] = defaultdict(lambda: defaultdict(list))
    
    for result in results:
        doc_key = result.doc_key or result.source_file or ""
        base_key = re.sub(r'[-_\.\(]v\d+[\)]?$', '', doc_key, flags=re.IGNORECASE)
        meta = result.metadata or {}
        version = meta.get("version", 0)
        version_key = f"{doc_key}|{version}"
        families[base_key][version_key].append(result)
    
    resolved: List[SearchResult] = []
    conflicts_detected = 0
    
    for base_key, versions in families.items():
        if len(versions) == 1:
            for chunks in versions.values():
                resolved.extend(chunks)
        else:
            version_reps = []
            for version_key, chunks in versions.items():
                max_freshness = max(c.freshness_score for c in chunks)
                version_reps.append((version_key, chunks, max_freshness))
            
            version_reps.sort(key=lambda x: x[2], reverse=True)
            winner_key, winner_chunks, winner_freshness = version_reps[0]
            stale_versions = version_reps[1:]
            
            conflicts_detected += 1
            logger.warning(
                "version_conflict_resolved",
                base_key=base_key,
                winner_key=winner_key,
                quarantined_versions=len(stale_versions),
            )
            resolved.extend(winner_chunks)
    
    if conflicts_detected > 0:
        logger.info("version_lineage_summary", conflicts_resolved=conflicts_detected)
    
    return resolved

def _safe_float(env_key: str, default: float) -> float:
    raw = os.getenv(env_key, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default

def apply_source_boost(results: List[SearchResult]) -> List[SearchResult]:
    if not results:
        return results

    pdf_boost = _safe_float("JARVIS_BOOST_PDF", 1.15)
    core_boost = _safe_float("JARVIS_BOOST_CORE", 1.20)
    long_boost = _safe_float("JARVIS_BOOST_LONG", 1.10)
    long_thresh = _safe_float("JARVIS_BOOST_LONG_THRESHOLD", 800.0)

    for res in results:
        boost = 1.0
        meta = res.metadata or {}
        domain = res.domain or meta.get("primary_domain") or meta.get("doc_primary_domain")
        source_file = res.source_file or meta.get("source_file") or ""
        text_len = len(res.text or "")

        if source_file.lower().endswith(".pdf"):
            boost *= pdf_boost

        if isinstance(domain, str) and domain == "jarvis.core":
            boost *= core_boost
        elif isinstance(meta.get("doc_primary_domain"), str) and meta.get("doc_primary_domain") == "jarvis.core":
            boost *= core_boost

        if text_len >= long_thresh:
            boost *= long_boost

        if boost != 1.0:
            res.score = float(res.score) * boost
            updated_meta = dict(meta)
            updated_meta.setdefault("original_score", float(res.score) / boost)
            updated_meta["boost_factor"] = float(boost)
            res.metadata = updated_meta

    results.sort(key=lambda r: r.score, reverse=True)
    return results

def apply_domain_prior(
    results: List[SearchResult],
    inferred_domains: List[str],
    mode: RetrievalMode,
) -> List[SearchResult]:
    if not results:
        return results
    
    inferred_lower = [d.lower() for d in inferred_domains]
    
    for r in results:
        domain = (r.domain or "").lower()
        meta = r.metadata or {}
        semantic_family = (meta.get("semantic_family") or "").lower()
        
        if mode == RetrievalMode.NORMAL:
            for inferred in inferred_lower:
                if domain.startswith(inferred) or inferred in domain:
                    r.score *= 1.2
                    break
            
            for inferred in inferred_lower:
                if semantic_family.startswith(inferred):
                    r.score *= 1.15
                    break
            
            if domain in ("jarvis-core", "jarvis.core") or semantic_family == "core-memory":
                r.score *= 0.4
        
        elif mode == RetrievalMode.META:
            if domain in ("jarvis-core", "jarvis.core") or semantic_family == "core-memory":
                r.score *= 1.25
    
    results.sort(key=lambda r: r.score, reverse=True)
    return results

def build_filter_for_mode(
    *,
    mode: RetrievalMode = RetrievalMode.NORMAL,
    domains: Optional[Sequence[str]] = None,
    tags: Optional[Sequence[str]] = None,
    include_system_docs: bool = False,
    allow_stale: bool = False,
    include_stale: bool = False,
    time_slice: Optional[Union[str, Tuple[str, str]]] = None,
) -> Optional[qmodels.Filter]:
    """Build Qdrant filter specific to retrieval mode."""
    # Merge stale flags (legacy support)
    allow_stale = allow_stale or include_stale

    must: List[qmodels.Condition] = []
    must_not: List[qmodels.Condition] = []
    should: List[qmodels.Condition] = []

    if domains:
        should.append(qmodels.FieldCondition(key="domain", match=qmodels.MatchAny(any=list(domains))))

    if tags:
        for tag in tags:
            must.append(qmodels.FieldCondition(key="tags", match=qmodels.MatchAny(any=[tag])))

    if not include_system_docs:
        must_not.append(qmodels.FieldCondition(key="is_system", match=qmodels.MatchValue(value=True)))

    if mode == RetrievalMode.NORMAL:
        if not allow_stale:
            must_not.append(qmodels.FieldCondition(key="semantic_family", match=qmodels.MatchValue(value="archive")))
            must.append(qmodels.FieldCondition(key="is_latest", match=qmodels.MatchValue(value=True)))

    elif mode == RetrievalMode.META:
        if not domains:
            must.append(qmodels.FieldCondition(key="domain", match=qmodels.MatchAny(any=["jarvis-core", "architecture", "epic", "story"])))
        if not allow_stale:
            must.append(qmodels.FieldCondition(key="is_latest", match=qmodels.MatchValue(value=True)))

    elif mode == RetrievalMode.TIME_SLICE:
        must.append(qmodels.FieldCondition(key="semantic_family", match=qmodels.MatchAny(any=["session-log", "epic", "story"])))
        if time_slice is not None:
            if isinstance(time_slice, tuple):
                start, end = time_slice
                must.append(qmodels.FieldCondition(key="session_date", range=qmodels.Range(gte=start, lte=end)))
            else:
                must.append(qmodels.FieldCondition(key="session_date", match=qmodels.MatchValue(value=time_slice)))

    if must or must_not or should:
        return qmodels.Filter(
            must=must if must else None,
            must_not=must_not if must_not else None,
            should=should if should else None
        )
    return None

def infer_query_domains(query: str) -> List[str]:
    q = query.lower()
    inferred: set[str] = set()

    if any(k in q for k in ["generative drive", "generativedrive", " gd ", "sines", "hydrogen", "water loop", "water-loop", "telemetry", "gd-"]):
        inferred.add("gd.generative_drive")
        inferred.add("gd")

    if any(k in q for k in ["epic ", "story ", "sprint ", "bmad"]):
        inferred.add("project.sprints")
        inferred.add("bmad.method")

    for needle, dom in CHAVAO_DOMAIN_MAP.items():
        if needle in q:
            inferred.add(dom)

    inferred.add("jarvis.conversations")
    inferred.add("jarvis.core")

    return list(inferred)

def filter_results_by_domains(results: List[SearchResult], domains: Optional[Sequence[str]]) -> List[SearchResult]:
    if not domains:
        return results
    allowed = {d.replace("-", ".") for d in domains if d}
    return [res for res in results if (res.domain or "").replace("-", ".") in allowed]

def normalize_domains_for_search(domains: Optional[Sequence[str]]) -> Optional[List[str]]:
    if not domains:
        return None
    normalized: List[str] = []
    for dom in domains:
        if not dom:
            continue
        normalized.append(dom.replace("-", "."))
    return normalized or None

def apply_time_weight(results: List[SearchResult]) -> List[SearchResult]:
    if not results:
        return results

    alpha_raw = os.getenv("JARVIS_TIME_WEIGHT_ALPHA", "").strip()
    try:
        alpha = float(alpha_raw) if alpha_raw else 0.2
    except ValueError:
        alpha = 0.2

    if alpha <= 0.0:
        return results

    step_values = []
    for res in results:
        meta = res.metadata or {}
        steps = meta.get("doc_step_count")
        if isinstance(steps, (int, float)) and steps > 0:
            step_values.append(float(steps))

    if not step_values:
        return results

    min_steps = min(step_values)
    max_steps = max(step_values)
    span = max_steps - min_steps
    if span <= 0.0:
        return results

    for res in results:
        meta = res.metadata or {}
        steps = meta.get("doc_step_count")
        if not isinstance(steps, (int, float)) or steps <= 0:
            continue
        norm = (float(steps) - min_steps) / span
        time_weight = 1.0 + alpha * norm

        updated_meta = dict(meta)
        updated_meta.setdefault("original_score", float(res.score))
        updated_meta["time_weight"] = float(time_weight)
        res.metadata = updated_meta
        res.score = float(res.score) * time_weight

    results.sort(key=lambda r: r.score, reverse=True)
    return results
