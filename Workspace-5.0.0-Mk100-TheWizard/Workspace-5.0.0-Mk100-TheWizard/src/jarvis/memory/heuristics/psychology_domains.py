"""Psychology and neuroscience domain mappings.

Covers clinical psychology, cognitive science, neuroscience, behavioral theory,
and specific attention/executive function topics relevant to ADHD context.
"""

from __future__ import annotations

from typing import Dict

# Keyword-based classification for psychology & neuroscience
PSYCHOLOGY_KEYWORD_MAP: Dict[str, str] = {
    # Neuroscience & Neurology (existing from old map)
    "neuron": "science.neurology",
    "neuronio": "science.neurology",
    "neurónio": "science.neurology",
    "synapse": "science.neurology",
    "sinapse": "science.neurology",
    "dopamine": "science.neurology",
    "serotonin": "science.neurology",
    "glutamate": "science.neurology",
    "gaba ": "science.neurology",
    "acetylcholine": "science.neurology",
    "neurotransmitter": "science.neurology",
    "neurotransmissor": "science.neurology",
    "neural network": "science.neuroscience",
    "brain connectivity": "science.neuroscience",
    "neuroplasticity": "science.neuroscience",
    "neuroimaging": "science.neuroscience",
    "fmri": "science.neuroscience",
    "eeg ": "science.neuroscience",
    "cortex": "science.neuroscience",
    "hippocampus": "science.neuroscience",
    "amygdala": "science.neuroscience",
    "prefrontal cortex": "science.neuroscience",

    # Cognitive Psychology & Neuroscience
    "cognitive psychology": "psychology.cognitive",
    "cognitive science": "science.cognitive",
    "working memory": "psychology.cognitive",
    "short-term memory": "psychology.cognitive",
    "long-term memory": "psychology.cognitive",
    "attention": "psychology.cognitive",
    "perception": "psychology.cognitive",
    "decision making": "psychology.cognitive",
    "problem solving": "psychology.cognitive",
    "reasoning": "psychology.cognitive",
    "cognitive load": "psychology.cognitive",

    # Executive Function & ADHD (critical for user context)
    "executive function": "psychology.executive_function",
    "executive dysfunction": "psychology.executive_function",
    "task switching": "psychology.executive_function",
    "cognitive control": "psychology.executive_function",
    "impulse control": "psychology.executive_function",
    "self-regulation": "psychology.executive_function",
    "adhd": "psychology.adhd",
    "attention deficit": "psychology.adhd",
    "hyperactivity": "psychology.adhd",
    "inattention": "psychology.adhd",
    "hyperfocus": "psychology.adhd",
    "time blindness": "psychology.adhd",
    "rejection sensitive dysphoria": "psychology.adhd",
    "rsd ": "psychology.adhd",

    # Behavioral Psychology
    "behavioral psychology": "psychology.behavioral",
    "behaviorism": "psychology.behavioral",
    "classical conditioning": "psychology.behavioral",
    "operant conditioning": "psychology.behavioral",
    "reinforcement": "psychology.behavioral",
    "punishment": "psychology.behavioral",
    "habit formation": "psychology.behavioral",
    "behavior modification": "psychology.behavioral",

    # Clinical Psychology
    "clinical psychology": "psychology.clinical",
    "psychotherapy": "psychology.clinical",
    "cognitive behavioral therapy": "psychology.clinical",
    "cbt ": "psychology.clinical",
    "dialectical behavior therapy": "psychology.clinical",
    "dbt ": "psychology.clinical",
    "mindfulness": "psychology.clinical",
    "mental health": "psychology.clinical",
    "anxiety": "psychology.clinical",
    "depression": "psychology.clinical",
    "trauma": "psychology.clinical",
    "ptsd": "psychology.clinical",

    # Social Psychology
    "social psychology": "psychology.social",
    "group dynamics": "psychology.social",
    "social cognition": "psychology.social",
    "attribution theory": "psychology.social",
    "conformity": "psychology.social",
    "persuasion": "psychology.social",
    "social influence": "psychology.social",

    # Developmental Psychology
    "developmental psychology": "psychology.developmental",
    "child development": "psychology.developmental",
    "cognitive development": "psychology.developmental",
    "lifespan development": "psychology.developmental",
    "attachment theory": "psychology.developmental",
}
