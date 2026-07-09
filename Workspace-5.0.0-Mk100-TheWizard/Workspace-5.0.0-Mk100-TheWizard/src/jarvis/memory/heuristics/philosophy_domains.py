"""Philosophy domain mappings.

Covers epistemology, ethics, logic, metaphysics, philosophy of mind,
philosophy of science, and technology ethics.
"""

from __future__ import annotations

from typing import Dict

# Keyword-based classification for philosophy
PHILOSOPHY_KEYWORD_MAP: Dict[str, str] = {
    # Epistemology (Theory of Knowledge)
    "epistemology": "philosophy.epistemology",
    "theory of knowledge": "philosophy.epistemology",
    "justified belief": "philosophy.epistemology",
    "skepticism": "philosophy.epistemology",
    "empiricism": "philosophy.epistemology",
    "rationalism": "philosophy.epistemology",
    "a priori": "philosophy.epistemology",
    "a posteriori": "philosophy.epistemology",
    "gettier problem": "philosophy.epistemology",

    # Ethics & Moral Philosophy
    "ethics": "philosophy.ethics",
    "moral philosophy": "philosophy.ethics",
    "deontology": "philosophy.ethics",
    "consequentialism": "philosophy.ethics",
    "utilitarianism": "philosophy.ethics",
    "virtue ethics": "philosophy.ethics",
    "moral relativism": "philosophy.ethics",
    "ethical dilemma": "philosophy.ethics",
    "applied ethics": "philosophy.ethics",
    "bioethics": "philosophy.ethics",
    "business ethics": "philosophy.ethics",

    # Logic & Reasoning
    "formal logic": "philosophy.logic",
    "propositional logic": "philosophy.logic",
    "predicate logic": "philosophy.logic",
    "modal logic": "philosophy.logic",
    "syllogism": "philosophy.logic",
    "logical fallacy": "philosophy.logic",
    "deductive reasoning": "philosophy.logic",
    "inductive reasoning": "philosophy.logic",
    "abductive reasoning": "philosophy.logic",

    # Metaphysics & Ontology
    "metaphysics": "philosophy.metaphysics",
    "ontology": "philosophy.metaphysics",
    "being and existence": "philosophy.metaphysics",
    "identity": "philosophy.metaphysics",
    "causality": "philosophy.metaphysics",
    "free will": "philosophy.metaphysics",
    "determinism": "philosophy.metaphysics",
    "compatibilism": "philosophy.metaphysics",
    "substance": "philosophy.metaphysics",

    # Philosophy of Mind & Consciousness
    "philosophy of mind": "philosophy.mind",
    "consciousness": "philosophy.mind",
    "qualia": "philosophy.mind",
    "mind-body problem": "philosophy.mind",
    "dualism": "philosophy.mind",
    "physicalism": "philosophy.mind",
    "functionalism": "philosophy.mind",
    "intentionality": "philosophy.mind",
    "mental states": "philosophy.mind",
    "hard problem of consciousness": "philosophy.mind",

    # Philosophy of Science
    "philosophy of science": "philosophy.science",
    "scientific method": "philosophy.science",
    "falsifiability": "philosophy.science",
    "paradigm shift": "philosophy.science",
    "kuhn ": "philosophy.science",
    "popper": "philosophy.science",
    "scientific realism": "philosophy.science",
    "instrumentalism": "philosophy.science",
    "demarcation problem": "philosophy.science",

    # Philosophy of Technology & AI Ethics
    "philosophy of technology": "philosophy.technology",
    "technology ethics": "philosophy.technology",
    "ai ethics": "philosophy.technology",
    "artificial intelligence ethics": "philosophy.technology",
    "ai alignment": "philosophy.technology",
    "ai safety": "philosophy.technology",
    "existential risk": "philosophy.technology",
    "superintelligence": "philosophy.technology",
    "technological determinism": "philosophy.technology",
    "digital ethics": "philosophy.technology",
    "algorithmic bias": "philosophy.technology",
    "data ethics": "philosophy.technology",
}
