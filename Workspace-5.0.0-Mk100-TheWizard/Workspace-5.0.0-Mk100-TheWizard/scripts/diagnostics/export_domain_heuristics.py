"""Export current domain heuristics to config/domain_heuristics.yaml.

This is a small helper for the lab environment: it generates a YAML (or JSON)
representation of the in-code heuristic maps so they can be tuned without
touching Python.

Usage (from repo root, inside the container):

    export PYTHONPATH=/workspace/src
    poetry run python scripts/export_domain_heuristics.py

This will create or overwrite `config/domain_heuristics.yaml`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import json


def main() -> None:
    # Import lazily so this script does not affect regular module loading.
    from jarvis.memory import domain_heuristics

    direct_domain_map = domain_heuristics.DIRECT_DOMAIN_MAP
    chavao_domain_map = domain_heuristics.CHAVAO_DOMAIN_MAP
    gd_keyword_tags = domain_heuristics.GD_KEYWORD_TAGS

    data: Dict[str, Dict[str, Any]] = {
        "direct_domain_map": dict(direct_domain_map),
        "chavao_domain_map": dict(chavao_domain_map),
        "gd_keyword_tags": dict(gd_keyword_tags),
    }

    config_dir = Path("config")
    config_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = config_dir / "domain_heuristics.yaml"

    try:
        import yaml  # type: ignore[import]
    except Exception:
        # Fall back to JSON if PyYAML is not available.
        json_path = config_dir / "domain_heuristics.json"
        json_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        print(f"Wrote domain heuristics config to {json_path}")
        return

    yaml_text = yaml.safe_dump(
        data,
        sort_keys=True,
        allow_unicode=True,
        default_flow_style=False,
    )
    yaml_path.write_text(yaml_text, encoding="utf-8")
    print(f"Wrote domain heuristics config to {yaml_path}")


if __name__ == "__main__":
    main()

