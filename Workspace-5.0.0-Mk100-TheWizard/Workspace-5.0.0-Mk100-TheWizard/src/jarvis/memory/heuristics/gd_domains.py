"""GenerativeDrive energy project domain mappings.

Covers renewable energy systems, hydrogen economy, smart grids, water loops,
and sustainability topics related to the GenerativeDrive Portugal energy project.

This is extracted from the original domain_heuristics.py GD_KEYWORD_TAGS.
"""

from __future__ import annotations

from typing import Dict

# Keyword → tag mapping for the Generative Drive / Sines energy model.
# These are used as additional tags once a chunk is known to be related
# to Generative Drive (via either explicit mention or strong context).
GD_KEYWORD_TAGS: Dict[str, str] = {
    # Location / project
    "sines": "sines",

    # Hydrogen (H2) – English + PT variants and abbreviations.
    "hydrogen": "hydrogen",
    "hidrog": "hydrogen",
    "hidrogénio": "hydrogen",
    "hidrogenio": "hydrogen",
    "hidrogênio": "hydrogen",
    "green hydrogen": "hydrogen_green",
    "hidrogénio verde": "hydrogen_green",
    "hidrogenio verde": "hydrogen_green",
    "hidrogênio verde": "hydrogen_green",
    " h2 ": "hydrogen",
    "[h2]": "hydrogen",

    # Solar
    "solar": "solar",
    "energia solar": "solar",
    "painel solar": "solar",
    "painéis solares": "solar",
    "painel fotovoltaico": "solar",
    "fotovoltaic": "solar",
    "photovoltaic": "solar",
    "pv ": "solar",

    # Wind / eolic
    "eolic": "wind",
    "eólico": "wind",
    "eolico": "wind",
    "wind": "wind",
    "energia eólica": "wind",
    "parque eólico": "wind",
    "parques eólicos": "wind",
    "wind farm": "wind",

    # Hydro
    "hydro": "hydro",
    "hídrica": "hydro",
    "hidrica": "hydro",
    "água": "water",
    "agua": "water",
    "barragem": "hydro",
    "barragens": "hydro",
    "hidroelétrica": "hydro",
    "hidroeletrica": "hydro",
    "hydroelectric": "hydro",
    "dam ": "hydro",

    # Smart grids
    "smart grid": "smart_grid",
    "smart-grid": "smart_grid",
    "smartgrids": "smart_grid",
    "smart grids": "smart_grid",
    "rede inteligente": "smart_grid",

    # AI / ML (overlaps with ai_ml_domains but kept for GD tagging)
    "inteligência artificial": "ai",
    "inteligencia artificial": "ai",
    " ai ": "ai",
    "machine learning": "ai",
    "aprendizagem automática": "ai",
    "aprendizagem automatica": "ai",
    "large language model": "ai",
    "modelo de linguagem": "ai",

    # Materials / sustainability
    "plastic": "plastics",
    "plástico": "plastics",
    "plastico": "plastics",
    "plásticos": "plastics",
    "microplastics": "plastics",
    "microplásticos": "plastics",

    # Water loops / circularity
    "water loop": "water_loops",
    "waterloop": "water_loops",
    "ciclo da água": "water_loops",
    "ciclo da agua": "water_loops",
    "water cycle": "water_loops",

    # Energy storage & batteries
    "battery": "energy_storage",
    "bateria": "energy_storage",
    "energy storage": "energy_storage",
    "armazenamento": "energy_storage",

    # Renewable energy general
    "renewable": "renewable_energy",
    "renovável": "renewable_energy",
    "renovavel": "renewable_energy",
    "clean energy": "renewable_energy",
    "energia limpa": "renewable_energy",
}
