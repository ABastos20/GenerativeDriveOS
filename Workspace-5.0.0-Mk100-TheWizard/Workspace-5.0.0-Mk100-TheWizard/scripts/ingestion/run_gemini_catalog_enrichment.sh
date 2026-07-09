#!/usr/bin/env bash
set -euo pipefail

#
# Full Gemini-powered domain catalog + enrichment job for the knowledge collection.
#
# This script is intended to be run inside the jarvis-app container:
#   docker exec -it jarvis-app bash -lc "bash scripts/run_gemini_catalog_enrichment.sh"
#
# Behavior:
#   1) Runs domain cataloging over the Qdrant "knowledge" collection using Google Gemini
#      via the google-ai provider, populating primary_domain/domains/rick_personas/tags.
#   2) Runs chunk enrichment over the same collection, generating per-chunk summary,
#      bullet-style facts, tags, and doc_type fields.
#   3) Respects environment overrides for provider/model/limits/batch sizes/domains.
#
# Environment overrides (optional):
#   JARVIS_ENRICH_PROVIDER   - LLM provider for catalog + enrichment (default: google-ai)
#   JARVIS_ENRICH_MODEL      - Model identifier for provider        (default: gemini-2.5)
#   JARVIS_CATALOG_LIMIT     - Max points to catalog (default: all)
#   JARVIS_ENRICH_LIMIT      - Max points to enrich  (default: all)
#   JARVIS_CATALOG_BATCH     - Catalog batch size (default: 64)
#   JARVIS_ENRICH_BATCH      - Enrich batch size (default: 16)
#   JARVIS_ENRICH_DOMAINS    - Comma-separated payload domains to enrich (default:
#                              "jarvis-core,jarvis-conversations,jarvis-insights")
#

export PYTHONPATH=/workspace/src
cd /workspace

PROVIDER="${JARVIS_ENRICH_PROVIDER:-google-ai}"
MODEL="${JARVIS_ENRICH_MODEL:-gemini-2.5}"
CATALOG_LIMIT="${JARVIS_CATALOG_LIMIT:-}"
ENRICH_LIMIT="${JARVIS_ENRICH_LIMIT:-}"
CATALOG_BATCH="${JARVIS_CATALOG_BATCH:-64}"
ENRICH_BATCH="${JARVIS_ENRICH_BATCH:-16}"
ENRICH_DOMAINS_DEFAULT="jarvis-core,jarvis-conversations,jarvis-insights"
ENRICH_DOMAINS="${JARVIS_ENRICH_DOMAINS:-$ENRICH_DOMAINS_DEFAULT}"

# Mirror defaults used in domain_catalog.py so we can see exactly
# what windowing settings Gemini is running with for this job.
# Python default is 2000 chars and 3 windows; env vars can override.
WINDOW_CHARS="${JARVIS_CATALOG_WINDOW_CHARS:-2000}"
MAX_WINDOWS="${JARVIS_CATALOG_MAX_WINDOWS:-3}"

# Simulation knobs (used only for the cost estimate below).
SIM_TOKENS_PER_CHUNK="${JARVIS_SIM_TOKENS_PER_CHUNK:-600}"
SIM_COST_PER_1K="${JARVIS_SIM_COST_PER_1K_TOKENS_USD:-0.0005}"

# Provider used for the usage summary (defaults to the enrich provider).
USAGE_PROVIDER="${JARVIS_USAGE_PROVIDER:-$PROVIDER}"

echo "🔧 Starting full Gemini catalog + enrichment job..."
echo "   Provider: ${PROVIDER}"
echo "   Model:    ${MODEL}"
echo "   Catalog:  batch=${CATALOG_BATCH}, limit=${CATALOG_LIMIT:-<all>}"
echo "   Enrich:   batch=${ENRICH_BATCH}, limit=${ENRICH_LIMIT:-<all>}, domains=${ENRICH_DOMAINS}"
echo "   Windows:  chars=${WINDOW_CHARS}, max_windows=${MAX_WINDOWS}"
echo "   Sim:      tokens_per_chunk=${SIM_TOKENS_PER_CHUNK}, cost_per_1k_tokens_usd=${SIM_COST_PER_1K}"
echo "   Usage:    provider=${USAGE_PROVIDER}"
echo ""

echo "📊 Simulating approximate job cost (offline estimate)..."
JARVIS_USAGE_PROVIDER="${USAGE_PROVIDER}" JARVIS_SIM_MODEL="${MODEL}" python - << 'PY'
import os
from decimal import Decimal

from sqlalchemy import func

from jarvis.database.qdrant import get_qdrant_client, get_collection_info
from jarvis.database.models import LLMProvider, LLMUsageLog
from jarvis.database.postgres import get_session

collection = "knowledge"
catalog_limit_raw = os.getenv("JARVIS_CATALOG_LIMIT") or ""
enrich_limit_raw = os.getenv("JARVIS_ENRICH_LIMIT") or ""

def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None

catalog_limit = _parse_int(catalog_limit_raw)
enrich_limit = _parse_int(enrich_limit_raw)

client = get_qdrant_client()
info = get_collection_info(collection, client=client)
points_total = int(info.points_count or 0)

catalog_points = min(points_total, catalog_limit) if catalog_limit is not None else points_total
enrich_points = min(points_total, enrich_limit) if enrich_limit is not None else points_total

# Heuristic: average 600 tokens per chunk (prompt+completion) and $0.0005 per 1K tokens.
tokens_per_chunk = float(os.getenv("JARVIS_SIM_TOKENS_PER_CHUNK", "600"))
cost_per_1k = float(os.getenv("JARVIS_SIM_COST_PER_1K_TOKENS_USD", "0.0005"))

total_chunks = catalog_points + enrich_points
estimated_tokens = total_chunks * tokens_per_chunk
estimated_cost = (estimated_tokens / 1000.0) * cost_per_1k

print(
    f"  Collection: {collection}, total_points={points_total}, "
    f"catalog_points={catalog_points}, enrich_points={enrich_points}"
)
print(
    "  Estimate "
    f"(tokens_per_chunk={tokens_per_chunk}, cost_per_1k_tokens_usd={cost_per_1k}): "
    f"~{int(estimated_tokens)} tokens, ~${estimated_cost:.4f} for this job"
)

# Also show current provider usage for context.
provider_name = os.getenv("JARVIS_USAGE_PROVIDER", "google-ai")
with get_session() as session:
    provider = (
        session.query(LLMProvider)
        .filter(LLMProvider.name == provider_name)
        .one_or_none()
    )

    if provider is None:
        print(f"  {provider_name}: no historical usage recorded yet.")
    else:
        tokens_in, tokens_out, cost = (
            session.query(
                func.coalesce(func.sum(LLMUsageLog.tokens_input), 0),
                func.coalesce(func.sum(LLMUsageLog.tokens_output), 0),
                func.coalesce(func.sum(LLMUsageLog.cost_usd), Decimal("0.0")),
            )
            .filter(LLMUsageLog.provider_id == provider.id)
            .one()
        )
        print(
            f"  Historical usage for {provider_name}: "
            f"tokens_in={tokens_in}, tokens_out={tokens_out}, cost_usd={cost}"
        )
PY
echo ""

echo "📈 LLM usage (before job):"
JARVIS_USAGE_PROVIDER="${PROVIDER}" python - << 'PY'
import os
from decimal import Decimal

from sqlalchemy import func

from jarvis.database.models import LLMProvider, LLMUsageLog
from jarvis.database.postgres import get_session

provider_name = os.getenv("JARVIS_USAGE_PROVIDER", "google-ai")

with get_session() as session:
    provider = (
        session.query(LLMProvider)
        .filter(LLMProvider.name == provider_name)
        .one_or_none()
    )

    if provider is None:
        print(f"{provider_name}: no usage recorded yet.")
    else:
        tokens_in, tokens_out, cost = (
            session.query(
                func.coalesce(func.sum(LLMUsageLog.tokens_input), 0),
                func.coalesce(func.sum(LLMUsageLog.tokens_output), 0),
                func.coalesce(func.sum(LLMUsageLog.cost_usd), Decimal("0.0")),
            )
            .filter(LLMUsageLog.provider_id == provider.id)
            .one()
        )
        print(
            f"{provider_name}: tokens_in={tokens_in}, "
            f"tokens_out={tokens_out}, cost_usd={cost}"
        )
PY
echo ""

CATALOG_ARGS=(
  "--collection" "knowledge"
  "--provider" "${PROVIDER}"
  "--model" "${MODEL}"
  "--batch-size" "${CATALOG_BATCH}"
)

if [[ -n "${CATALOG_LIMIT}" ]]; then
  CATALOG_ARGS+=("--limit" "${CATALOG_LIMIT}")
fi

echo "📚 Step 1/2: Cataloging domains with Gemini (jarvis-core + conversations + others)..."
python -m jarvis.cli.analytics catalog-domains "${CATALOG_ARGS[@]}"
echo ""

ENRICH_ARGS=(
  "--collection" "knowledge"
  "--provider" "${PROVIDER}"
  "--model" "${MODEL}"
  "--batch-size" "${ENRICH_BATCH}"
  "--domains" "${ENRICH_DOMAINS}"
)

if [[ -n "${ENRICH_LIMIT}" ]]; then
  ENRICH_ARGS+=("--limit" "${ENRICH_LIMIT}")
fi

echo "🧠 Step 2/2: Enriching chunks (summary/facts/tags/doc_type) with Gemini..."
python -m jarvis.cli.analytics enrich-chunks "${ENRICH_ARGS[@]}"
echo ""

echo "✅ Gemini catalog + enrichment job completed."

echo ""
echo "📈 LLM usage (after job):"
JARVIS_USAGE_PROVIDER="${PROVIDER}" python - << 'PY'
import os
from decimal import Decimal

from sqlalchemy import func

from jarvis.database.models import LLMProvider, LLMUsageLog
from jarvis.database.postgres import get_session

provider_name = os.getenv("JARVIS_USAGE_PROVIDER", "google-ai")

with get_session() as session:
    provider = (
        session.query(LLMProvider)
        .filter(LLMProvider.name == provider_name)
        .one_or_none()
    )

    if provider is None:
        print(f"{provider_name}: no usage recorded yet.")
    else:
        tokens_in, tokens_out, cost = (
            session.query(
                func.coalesce(func.sum(LLMUsageLog.tokens_input), 0),
                func.coalesce(func.sum(LLMUsageLog.tokens_output), 0),
                func.coalesce(func.sum(LLMUsageLog.cost_usd), Decimal("0.0")),
            )
            .filter(LLMUsageLog.provider_id == provider.id)
            .one()
        )
        print(
            f"{provider_name}: tokens_in={tokens_in}, "
            f"tokens_out={tokens_out}, cost_usd={cost}"
        )
PY
