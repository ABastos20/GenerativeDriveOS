"""Prompt building for RAG queries."""
from typing import List

from jarvis.memory import search


def build_rag_prompt(
    question: str,
    results: List[search.SearchResult],
    grounding_level: str,
) -> tuple[str, str, list]:
    """Build system and user prompts for RAG.
    
    Returns:
        (system_prompt, user_prompt, citations)
    """
    context_parts = []
    citations = []

    for idx, res in enumerate(results, start=1):
        # Format citation reference
        source_ref = f"[{idx}]"
        if res.source_file:
            source_info = f"{res.source_file}"
            if res.section:
                source_info += f" (section: {res.section})"
            source_ref += f" {source_info}"
        elif res.domain:
            source_ref += f" domain:{res.domain.replace('.', '-')}"

        citations.append({
            "id": idx,
            "source_file": res.source_file,
            "section": res.section,
            "domain": (res.domain or None).replace(".", "-") if res.domain else None,
            "score": round(res.score, 3),
        })

        # Add to context
        context_parts.append(f"[Source {idx}]\\n{res.text.strip()}")

    # Build RAG prompt
    context_block = "\\n\\n".join(context_parts)

    system_prompt = """You are JARVIS, an AI advisor with access to a curated knowledge base.

Answer the user's question based ONLY on the provided context sources.
- When the context contains both user-defined designs / models / plans and more generic or real-world reference material, treat the user-defined content as PRIMARY.
- Summarise and reason from the user-defined design or internal specification first.
- Mention real-world or external projects only as clearly labeled comparison or background (for example in a short 'Real-world context' note), and do not allow them to override or replace the user's design.
- Cite sources using [1], [2], etc. when referencing specific information.
- If the context doesn't contain enough information, say so clearly.
- Be concise and precise.
- Maintain technical accuracy.
"""

    if grounding_level == "soft":
        system_prompt += """
GROUNDING LEVEL: SOFT
- Be creative, but still tie specific claims to the provided sources.
- If you add bridging/speculative ideas, mark them as speculative and do not cite them.
- Never fabricate citations; only cite retrieved snippets.
"""
    elif grounding_level == "balanced":
        system_prompt += """
GROUNDING LEVEL: BALANCED
- Every major factual claim should cite a retrieved source.
- If a detail is not present, say it is not in memory instead of inventing it.
- You may include brief speculative glue, but label it as speculative (no source).
"""
    elif grounding_level == "strict":
        system_prompt += """
GROUNDING LEVEL: STRICT
- Do NOT invent new facts, entities, metrics, or examples that are not explicitly present in the context.
- Do NOT infer or guess additional background stories, telemetry, or architectures beyond what is written.
- If the context is insufficient to answer the question, respond with a short explanation that the answer cannot be derived from the provided sources.
- You are not producing original coherent thoughts; you are only summarising and reorganising the exact information present in the context snippets and citations. If needed, list the most relevant snippets and sources instead of speculating.
STRICT MODE IS ENABLED. Do not deviate from sources.
"""

    user_prompt = f"""Context from knowledge base:

{context_block}

---

Question: {question}

Answer the question based on the context above, citing sources where appropriate:"""

    return system_prompt, user_prompt, citations
