"""Hard sciences domain mappings.

Covers physics, mathematics, chemistry, biology, and neuroscience.
Includes existing mappings from the old domain_heuristics.py plus expansions.
"""

from __future__ import annotations

from typing import Dict

# Keyword-based classification for hard sciences
SCIENCE_KEYWORD_MAP: Dict[str, str] = {
    # Mathematics - Geometry & Calculus (existing from old map)
    "riemann curvature": "math.riemann_geometry",
    "riemann tensor": "math.riemann_geometry",
    "riemann ": "math.riemann_geometry",
    "curvature tensor": "math.riemann_geometry",
    "christoffel symbol": "math.riemann_geometry",
    "geodesic": "math.geometry",
    "manifold": "math.geometry",
    "differential geometry": "math.geometry",
    "topology": "math.geometry",

    # Mathematics - Physics & Mechanics (existing)
    "lagrangian": "math.physics",
    "euler-lagrange": "math.physics",
    "hamiltonian": "math.physics",
    "action principle": "math.physics",

    # Mathematics - Calculus (existing + expansion)
    "gradient": "math.calculus",
    "divergence": "math.calculus",
    "curl ": "math.calculus",
    "tensor calculus": "math.calculus",
    "vector calculus": "math.calculus",
    "partial derivative": "math.calculus",
    "differential equation": "math.differential_equations",
    "ode ": "math.differential_equations",
    "pde ": "math.differential_equations",
    "ordinary differential": "math.differential_equations",
    "partial differential": "math.differential_equations",

    # Mathematics - Transforms (existing)
    "fourier transform": "math.fourier",
    "laplace transform": "math.laplace",
    "wavelet transform": "math.transforms",

    # Mathematics - Other
    "linear algebra": "math.linear_algebra",
    "matrix": "math.linear_algebra",
    "eigenvalue": "math.linear_algebra",
    "eigenvector": "math.linear_algebra",
    "probability": "math.probability",
    "statistics": "math.statistics",
    "bayesian": "math.statistics",

    # Physics - General (existing + expansion)
    "physics": "science.physics",
    "física": "science.physics",
    "fisica": "science.physics",
    "theoretical physics": "science.physics",
    "experimental physics": "science.physics",

    # Physics - Quantum Mechanics (existing)
    "quantum": "science.physics.quantum",
    "quantum mechanics": "science.physics.quantum",
    "quantum field theory": "science.physics.quantum",
    "qft ": "science.physics.quantum",
    "schrodinger": "science.physics.quantum",
    "schrödinger": "science.physics.quantum",
    "heisenberg": "science.physics.quantum",
    "wave function": "science.physics.quantum",
    "superposition": "science.physics.quantum",
    "entanglement": "science.physics.quantum",

    # Physics - Relativity (existing + expansion)
    "einstein": "science.physics.relativity",
    "general relativity": "science.physics.relativity",
    "special relativity": "science.physics.relativity",
    "spacetime": "science.physics.relativity",
    "black hole": "science.physics.relativity",
    "event horizon": "science.physics.relativity",
    "gravitational wave": "science.physics.relativity",

    # Physics - Thermodynamics
    "thermodynamics": "science.physics.thermo",
    "entropy": "science.physics.thermo",
    "heat transfer": "science.physics.thermo",
    "statistical mechanics": "science.physics.thermo",
    "boltzmann": "science.physics.thermo",

    # Physics - Electromagnetism
    "electromagnetism": "science.physics.electromag",
    "maxwell equations": "science.physics.electromag",
    "electromagnetic": "science.physics.electromag",
    "electric field": "science.physics.electromag",
    "magnetic field": "science.physics.electromag",

    # Physics - Astrophysics (existing + expansion)
    "astrophysics": "science.physics.astrophysics",
    "cosmology": "science.physics.astrophysics",
    "galaxy": "science.physics.astrophysics",
    "star formation": "science.physics.astrophysics",
    "dark matter": "science.physics.astrophysics",
    "dark energy": "science.physics.astrophysics",
    "big bang": "science.physics.astrophysics",

    # Chemistry - General (existing)
    "chemistry": "science.chemistry",
    "química": "science.chemistry",
    "quimica": "science.chemistry",

    # Chemistry - Organic
    "organic chemistry": "science.chemistry.organic",
    "hydrocarbon": "science.chemistry.organic",
    "functional group": "science.chemistry.organic",
    "aromatic": "science.chemistry.organic",

    # Chemistry - Inorganic
    "inorganic chemistry": "science.chemistry.inorganic",
    "coordination complex": "science.chemistry.inorganic",
    "crystal structure": "science.chemistry.inorganic",

    # Chemistry - Physical
    "physical chemistry": "science.chemistry.physical",
    "chemical kinetics": "science.chemistry.physical",
    "thermochemistry": "science.chemistry.physical",
    "spectroscopy": "science.chemistry.physical",

    # Chemistry - Biochemistry
    "biochemistry": "science.chemistry.biochem",
    "enzyme": "science.chemistry.biochem",
    "protein structure": "science.chemistry.biochem",
    "metabolic pathway": "science.chemistry.biochem",

    # Biology - General (existing)
    "biology": "science.biology",
    "biologia": "science.biology",

    # Biology - Molecular
    "molecular biology": "science.biology.molecular",
    "dna ": "science.biology.molecular",
    "rna ": "science.biology.molecular",
    "gene expression": "science.biology.molecular",
    "transcription": "science.biology.molecular",
    "translation": "science.biology.molecular",

    # Biology - Cellular
    "cell biology": "science.biology.cellular",
    "cellular biology": "science.biology.cellular",
    "cell membrane": "science.biology.cellular",
    "mitochondria": "science.biology.cellular",
    "cell signaling": "science.biology.cellular",

    # Biology - Genetics
    "genetics": "science.biology.genetics",
    "genome": "science.biology.genetics",
    "genomics": "science.biology.genetics",
    "mutation": "science.biology.genetics",
    "evolution": "science.biology.genetics",
    "natural selection": "science.biology.genetics",
    "crispr": "science.biology.genetics",

    # Biology - Ecology
    "ecology": "science.biology.ecology",
    "ecosystem": "science.biology.ecology",
    "biodiversity": "science.biology.ecology",
    "conservation": "science.biology.ecology",
    "systems biology": "science.biology.ecology",
}
