"""Heuristic configuration for Jarvis domain cataloging.

This module aggregates domain classification heuristics from specialized
submodules organized by discipline. The taxonomy covers ~170 domains spanning:

- **JARVIS Core**: System internals, memory, agents, LLM providers, APIs
- **Cybersecurity**: Threat intel, PKI, SIEM, vulnerability management
- **Telecom/Network**: Carrier systems, telemetry, routing, OSS/BSS
- **Banking/Finance**: Banking systems, trading, risk, regulatory compliance
- **Psychology**: Neuroscience, ADHD, executive function, clinical psych
- **Philosophy**: Epistemology, ethics, logic, AI ethics
- **Hard Sciences**: Physics, math, chemistry, biology
- **AI/ML**: Deep learning, NLP, LLMs, RAG, embeddings, agents
- **Enterprise**: Architecture, consulting, cloud, digital transformation
- **BMAD Method**: Workflows, agents, patterns, project management
- **GenerativeDrive**: Renewable energy, hydrogen, smart grids
- **Dev/Infra**: Frameworks, containers, databases, CI/CD

## Architecture

Domain heuristics are organized into submodules under ``heuristics/``:

- ``jarvis_domains.py`` - JARVIS system domains
- ``cyber_domains.py`` - Cybersecurity domains
- ``telecom_domains.py`` - Telecom & networking domains
- ``finance_domains.py`` - Banking & finance domains
- ``psychology_domains.py`` - Psychology & neuroscience domains
- ``philosophy_domains.py`` - Philosophy domains
- ``science_domains.py`` - Physics, math, chemistry, biology
- ``ai_ml_domains.py`` - AI & machine learning domains
- ``enterprise_domains.py`` - Enterprise & consulting domains
- ``bmad_domains.py`` - BMAD methodology domains
- ``gd_domains.py`` - GenerativeDrive project domains
- ``dev_infra_domains.py`` - Development & infrastructure domains

This module exports aggregated dictionaries for use by ``domain_catalog.py``:

- **DIRECT_DOMAIN_MAP**: Raw payload ``domain`` values → canonical keys
- **CHAVAO_DOMAIN_MAP**: Keyword → primary_domain (consolidated from all submodules)
- **GD_KEYWORD_TAGS**: GenerativeDrive-specific tags (separate for GD context tagging)

## Usage

```python
from jarvis.memory.domain_heuristics import (
    DIRECT_DOMAIN_MAP,
    CHAVAO_DOMAIN_MAP,
    GD_KEYWORD_TAGS,
)
```

Heuristics are applied in ``domain_catalog._heuristic_metadata_from_payload()``
before falling back to expensive LLM classification calls.
"""

from __future__ import annotations

from pathlib import Path
import os
from typing import Dict, Tuple, Any

import json

# Import all domain mappings from submodules
from jarvis.memory.heuristics.ai_ml_domains import AI_ML_KEYWORD_MAP
from jarvis.memory.heuristics.bmad_domains import BMAD_KEYWORD_MAP
from jarvis.memory.heuristics.cyber_domains import CYBER_KEYWORD_MAP
from jarvis.memory.heuristics.dev_infra_domains import DEV_INFRA_KEYWORD_MAP
from jarvis.memory.heuristics.enterprise_domains import ENTERPRISE_KEYWORD_MAP
from jarvis.memory.heuristics.finance_domains import FINANCE_KEYWORD_MAP
from jarvis.memory.heuristics.gd_domains import GD_KEYWORD_TAGS as GD_KEYWORD_TAGS_DEFAULT
from jarvis.memory.heuristics.jarvis_domains import (
    JARVIS_DIRECT_DOMAIN_MAP,
    JARVIS_KEYWORD_MAP,
)
from jarvis.memory.heuristics.philosophy_domains import PHILOSOPHY_KEYWORD_MAP
from jarvis.memory.heuristics.psychology_domains import PSYCHOLOGY_KEYWORD_MAP
from jarvis.memory.heuristics.science_domains import SCIENCE_KEYWORD_MAP
from jarvis.memory.heuristics.telecom_domains import TELECOM_KEYWORD_MAP

# =============================================================================
# DIRECT_DOMAIN_MAP - Raw payload "domain" values → canonical keys
# =============================================================================
# This handles direct mappings from ingested payload values to our canonical
# domain keys. Used when chunks already have explicit domain metadata.


def _build_from_submodules() -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """Build heuristics purely from Python submodules.

    This is the original behaviour and acts as a fallback when no
    config/domain_heuristics.{yaml,json} file is present.
    """
    direct_domain_map: Dict[str, str] = {
        **JARVIS_DIRECT_DOMAIN_MAP,
        # Note: Most direct mappings are in JARVIS domains since they come from
        # our own ingestion pipeline. Other disciplines don't have payload-level
        # domain values in most cases.
    }

    # Generic keyword ("chavões") → primary_domain mapping, aggregated from all
    # discipline-specific submodules. These are used when we still do not have a
    # strong primary domain from other signals (folder, explicit domain, etc.).
    #
    # This is the main heuristic map used by domain_catalog for zero-LLM
    # classification.
    chavao_domain_map: Dict[str, str] = {
        **JARVIS_KEYWORD_MAP,
        **CYBER_KEYWORD_MAP,
        **TELECOM_KEYWORD_MAP,
        **FINANCE_KEYWORD_MAP,
        **PSYCHOLOGY_KEYWORD_MAP,
        **PHILOSOPHY_KEYWORD_MAP,
        **SCIENCE_KEYWORD_MAP,
        **AI_ML_KEYWORD_MAP,
        **ENTERPRISE_KEYWORD_MAP,
        **BMAD_KEYWORD_MAP,
        **DEV_INFRA_KEYWORD_MAP,
        # Note: GD_KEYWORD_TAGS_DEFAULT is kept separate (below) since it's used
        # specifically for tag enrichment within GD-context chunks, not for
        # primary_domain classification.
    }

    gd_keyword_tags: Dict[str, str] = dict(GD_KEYWORD_TAGS_DEFAULT)

    return direct_domain_map, chavao_domain_map, gd_keyword_tags


def _load_from_config() -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """Load heuristics from config/domain_heuristics.(yaml|json) and overlay them.

    Expected structure:

    ```yaml
    direct_domain_map:
      raw_domain_value: canonical.domain.key

    chavao_domain_map:
      keyword: primary.domain.key

    gd_keyword_tags:
      keyword: tag_key
    ```

    The file is optional. If it is missing, callers should fall back to
    :func:`_build_from_submodules`. When present, the config acts as a
    plugin/override layer **on top of** the Python heuristics, so you can
    add or override entries without duplicating the full map.
    """
    base_direct, base_chavao, base_gd = _build_from_submodules()

    config_dir = Path("config")
    yaml_path = config_dir / "domain_heuristics.yaml"
    json_path = config_dir / "domain_heuristics.json"

    if yaml_path.exists():
        config_text = yaml_path.read_text(encoding="utf-8")
        try:
            import yaml  # type: ignore[import]
        except Exception as exc:  # pragma: no cover - very rare
            raise RuntimeError(
                "config/domain_heuristics.yaml exists but PyYAML is not available. "
                "Install pyyaml or remove the file."
            ) from exc

        data: Dict[str, Any] = yaml.safe_load(config_text) or {}
    elif json_path.exists():
        config_text = json_path.read_text(encoding="utf-8")
        data = json.loads(config_text)
    else:
        raise FileNotFoundError("No domain_heuristics config file found.")

    direct_domain_map = dict(base_direct)
    direct_domain_map.update(
        {
            str(key): str(value)
            for key, value in (data.get("direct_domain_map") or {}).items()
        }
    )

    chavao_domain_map = dict(base_chavao)
    chavao_domain_map.update(
        {
            str(key): str(value)
            for key, value in (data.get("chavao_domain_map") or {}).items()
        }
    )

    gd_keyword_tags = dict(base_gd)
    gd_keyword_tags.update(
        {
            str(key): str(value)
            for key, value in (data.get("gd_keyword_tags") or {}).items()
        }
    )

    return direct_domain_map, chavao_domain_map, gd_keyword_tags


_USE_CONFIG = os.getenv("JARVIS_DOMAIN_HEURISTICS_CONFIG", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

if _USE_CONFIG:
    try:
        # Prefer config-driven heuristics if explicitly enabled via env var.
        # This allows different workspaces (lab vs CGD, etc.) to tune mappings
        # without changing Python code. If the file is missing, fall back to
        # the built-in maps.
        DIRECT_DOMAIN_MAP, CHAVAO_DOMAIN_MAP, GD_KEYWORD_TAGS = _load_from_config()
    except FileNotFoundError:
        DIRECT_DOMAIN_MAP, CHAVAO_DOMAIN_MAP, GD_KEYWORD_TAGS = _build_from_submodules()
else:
    # Default for the lab: always use the Python heuristics.
    DIRECT_DOMAIN_MAP, CHAVAO_DOMAIN_MAP, GD_KEYWORD_TAGS = _build_from_submodules()


__all__ = ["DIRECT_DOMAIN_MAP", "CHAVAO_DOMAIN_MAP", "GD_KEYWORD_TAGS"]
