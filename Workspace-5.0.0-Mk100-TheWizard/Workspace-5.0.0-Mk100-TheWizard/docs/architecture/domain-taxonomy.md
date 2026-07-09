# Jarvis Domain Taxonomy

**Status**: Production
**Last Updated**: 2025-12-02
**Coverage**: 166 domains, 881 keyword mappings

---

## Overview

The Jarvis domain taxonomy is a hierarchical classification system that organizes knowledge across **12 major disciplines** spanning a polymath's digital brain. This taxonomy powers the domain cataloging system, enabling zero-LLM chunk classification through heuristics before falling back to expensive LLM calls.

**From 454 knowledge files** across OSS telecom, energy systems, security, banking, psychology, philosophy, AI, and more—this taxonomy provides comprehensive coverage for:

- Technical documentation (Cisco/Nokia telemetry, network configs)
- Energy project artifacts (GenerativeDrive hydrogen models, smart grids)
- Scientific papers (physics, chemistry, biology, neuroscience)
- Enterprise consulting work (NTT DATA projects, digital transformation)
- Personal knowledge (ADHD/executive function, philosophy)
- JARVIS system internals (memory, agents, LLM providers)

---

## Architecture

### Directory Structure

```
src/jarvis/memory/
├── domain_heuristics.py          # Main aggregator module
├── domain_catalog.py              # Uses heuristics for classification
├── validate_domains.py            # Taxonomy validator
└── heuristics/                    # Discipline-specific mappings
    ├── __init__.py
    ├── jarvis_domains.py          # JARVIS Core (20 domains)
    ├── cyber_domains.py           # Cybersecurity (13 domains)
    ├── telecom_domains.py         # Telecom/Network (22 domains)
    ├── finance_domains.py         # Banking/Finance (10 domains)
    ├── psychology_domains.py      # Psychology (7 domains)
    ├── philosophy_domains.py      # Philosophy (7 domains)
    ├── science_domains.py         # Physics/Math/Chem/Bio (30 domains)
    ├── ai_ml_domains.py           # AI/ML (15 domains)
    ├── enterprise_domains.py      # Consulting (6 domains)
    ├── bmad_domains.py            # BMAD Method (5 domains)
    ├── gd_domains.py              # GenerativeDrive (tags, not domains)
    └── dev_infra_domains.py       # Dev/Infra (24 domains)
```

### Exported Dictionaries

1. **`DIRECT_DOMAIN_MAP`**: Raw payload `domain` values → canonical keys (5 entries)
2. **`CHAVAO_DOMAIN_MAP`**: Keyword → `primary_domain` mappings (881 entries)
3. **`GD_KEYWORD_TAGS`**: GenerativeDrive tag enrichment (72 tags, separate from domains)

### Config Overrides (`config/domain_heuristics.yaml`)

In the lab we increasingly want to tune heuristics without touching Python.  
`domain_heuristics.py` therefore supports an optional config file:

```yaml
direct_domain_map:
  raw_domain_value: canonical.domain.key

chavao_domain_map:
  keyword: primary.domain.key

gd_keyword_tags:
  keyword: tag_key
```

- If `config/domain_heuristics.yaml` (or `.json`) is present, it is loaded and
  used as the source of truth.
- If it is missing, `domain_heuristics.py` falls back to the in-code maps from
  the `heuristics/` submodules.
- You can export the current in-code heuristics into a config file via:

  ```bash
  cd /workspace
  export PYTHONPATH=/workspace/src
  poetry run python scripts/export_domain_heuristics.py
  ```

This keeps the taxonomy authoritative while allowing workspace‑specific
overrides (e.g., Jarvis lab vs CGD) via simple config changes.

---

## Taxonomy Hierarchy

### Level 1: Top-Level Categories (17)

| Category | Domains | Description |
|----------|---------|-------------|
| **jarvis** | 20 | JARVIS system internals (memory, agents, API, LLM) |
| **science** | 19 | Hard sciences (neuroscience, neurology, astrophysics) |
| **network** | 17 | Networking infrastructure (Cisco, Nokia, telemetry) |
| **ai** | 15 | AI/ML (LLMs, RAG, embeddings, deep learning) |
| **infra** | 14 | Infrastructure (Docker, Kubernetes, Qdrant, Postgres) |
| **cyber** | 13 | Cybersecurity (STIX, PKI, SIEM, threat intel) |
| **math** | 11 | Mathematics (geometry, calculus, physics) |
| **dev** | 10 | Software development (frameworks, languages) |
| **philosophy** | 7 | Philosophy (epistemology, ethics, logic, mind) |
| **psychology** | 7 | Psychology (ADHD, cognitive, clinical) |
| **enterprise** | 6 | Enterprise architecture & consulting |
| **finance** | 6 | Banking & finance systems |
| **telecom** | 5 | Telecom carrier systems (OSS/BSS, 5G) |
| **project** | 5 | Project management (epics, stories, sprints) |
| **bmad** | 5 | BMAD methodology |
| **economics** | 4 | Economics (macro, micro, trade, energy) |
| **ntt_data** | 2 | NTT DATA client projects |

---

## Domain Coverage by Discipline

### 1. JARVIS Core (20 domains)

Jarvis' self-awareness layer - understanding its own architecture.

```
jarvis.core                # Core system
jarvis.architecture        # Technical architecture, PRD
jarvis.memory              # RAG system, vector store
jarvis.memory.rag          # Query expansion, RRF, hybrid retrieval
jarvis.memory.ingestion    # Document ingestion pipeline
jarvis.memory.compilation  # Knowledge compilation
jarvis.agents              # Council of Ricks, multi-agent
jarvis.personas            # Persona configs, weighted voting
jarvis.workflows           # BMAD workflow integration
jarvis.llm                 # Provider management, fallback chains
jarvis.api                 # REST API, FastAPI
jarvis.mcp                 # MCP server integration
jarvis.cli                 # Typer CLI commands
jarvis.database            # PostgreSQL, Qdrant schemas
jarvis.config              # Settings, secrets management
jarvis.playbooks           # User playbooks (architect-meeting-prep)
jarvis.conversations       # Conversation storage
jarvis.gpt_export          # GPT conversation exports
jarvis.user_snapshot       # User export snapshots
jarvis.insights            # Analytics, citation provenance
```

**Keywords**: jarvis memory, council of ricks, persona registry, llm provider, mcp server, query expansion, hybrid retrieval

---

### 2. Cybersecurity (13 domains)

Threat intelligence, PKI, vulnerability management, security tools.

```
cyber.security             # Generic security (policies, frameworks)
cyber.threat_intel         # MITRE ATT&CK, threat hunting
cyber.stix                 # STIX 2.1, TAXII
cyber.network_security     # Firewalls, IDS/IPS, zero trust
cyber.pki                  # SSL/TLS, certificates, encryption
cyber.iam                  # Identity & access management, MFA
cyber.siem                 # SIEM, Splunk, ELK
cyber.soc                  # Security operations center, SOAR
cyber.incident_response    # IR, forensics, malware analysis
cyber.vulnerability        # Vuln management, CVE, pen testing
cyber.tenable              # Tenable Nessus scanner
cyber.compliance           # ISO 27001, NIST, PCI-DSS, GDPR
cyber.cisco_security       # Cisco ASA, Firepower
```

**Keywords**: mitre att&ck, stix 2.1, tenable nessus, cisco asa, ssl/tls, pki, siem, incident response

---

### 3. Telecom/Networking (22 domains)

Carrier-grade systems, telemetry, routing protocols, OSS/BSS.

```
network.core               # Generic networking
network.cisco              # Cisco routers/switches
network.cisco.asa          # Cisco ASA firewall
network.cisco.telemetry    # Cisco telemetry, TLS configs
network.nokia              # Nokia networking
network.nokia.sros         # Nokia SR OS
network.telemetry          # SNMP, NetFlow, gRPC, YANG
network.bgp                # Border Gateway Protocol
network.ospf               # OSPF routing
network.isis               # IS-IS routing
network.routing            # Generic routing
network.mpls               # MPLS, VPN, L2/L3VPN
network.vpn                # VPN, IPsec
network.sdn                # Software-defined networking, NFV
network.overlay            # VXLAN, Geneve
network.vxlan              # VXLAN specifically
network.qos                # Quality of service, traffic engineering
telecom.oss                # Operations Support Systems
telecom.bss                # Business Support Systems
telecom.carrier            # Carrier-grade, DWDM, optical
telecom.5g                 # 5G core, RAN
telecom.mobile             # LTE, 4G, mobile networks
```

**Keywords**: cisco telemetry, nokia sros, snmp, netflow, bgp, ospf, mpls, oss/bss, 5g

---

### 4. Banking/Finance/Economics (10 domains)

Financial systems, trading, risk, regulatory compliance.

```
finance.banking            # Core banking, central banks
finance.payments           # SWIFT, SEPA, payment processing
finance.trading            # Algorithmic trading, HFT, exchanges
finance.risk               # VaR, stress testing, risk models
finance.compliance         # Basel III, PCI-DSS, AML, KYC
finance.blockchain         # Blockchain, crypto, DeFi
economics.macro            # Macroeconomics, monetary policy, GDP
economics.micro            # Microeconomics, supply/demand
economics.trade            # International trade, supply chains
economics.energy           # Energy economics, energy markets
```

**Keywords**: core banking, swift, basel iii, trading system, risk management, blockchain, gdp, energy economics

---

### 5. Psychology & Neuroscience (7 domains)

Clinical psych, cognitive science, ADHD, executive function.

```
psychology.cognitive       # Working memory, attention, perception
psychology.executive_function  # Task switching, cognitive control
psychology.adhd            # ADHD, hyperfocus, time blindness
psychology.behavioral      # Behaviorism, conditioning, reinforcement
psychology.clinical        # CBT, DBT, psychotherapy, mental health
psychology.social          # Group dynamics, social cognition
psychology.developmental   # Child development, attachment theory
science.neurology          # Neurons, neurotransmitters, synapses
science.neuroscience       # fMRI, EEG, neuroplasticity, cortex
science.cognitive          # Cognitive neuroscience
```

**Keywords**: adhd, executive function, working memory, dopamine, serotonin, cbt, neuron, synapse, prefrontal cortex

---

### 6. Philosophy (7 domains)

Epistemology, ethics, logic, philosophy of mind, AI ethics.

```
philosophy.epistemology    # Theory of knowledge, skepticism
philosophy.ethics          # Moral philosophy, utilitarianism
philosophy.logic           # Formal logic, deductive reasoning
philosophy.metaphysics     # Ontology, free will, determinism
philosophy.mind            # Consciousness, qualia, mind-body problem
philosophy.science         # Philosophy of science, falsifiability
philosophy.technology      # AI ethics, algorithmic bias, digital ethics
```

**Keywords**: epistemology, ethics, logic, consciousness, ai ethics, free will, philosophy of science

---

### 7. Hard Sciences (30 domains)

Physics, mathematics, chemistry, biology.

```
# Mathematics (11 domains)
math.riemann_geometry      # Riemann curvature, geodesics
math.geometry              # Manifolds, topology
math.physics               # Lagrangian, Hamiltonian mechanics
math.calculus              # Gradient, divergence, curl
math.differential_equations # ODE, PDE
math.fourier               # Fourier transforms
math.laplace               # Laplace transforms
math.transforms            # Wavelet transforms
math.linear_algebra        # Matrices, eigenvalues
math.probability           # Probability theory
math.statistics            # Statistics, Bayesian methods

# Physics (8 domains)
science.physics            # General physics
science.physics.quantum    # Quantum mechanics, QFT, Schrödinger
science.physics.relativity # General/special relativity, black holes
science.physics.thermo     # Thermodynamics, entropy
science.physics.electromag # Electromagnetism, Maxwell equations
science.physics.astrophysics # Cosmology, dark matter, big bang

# Chemistry (5 domains)
science.chemistry          # General chemistry
science.chemistry.organic  # Organic chemistry, hydrocarbons
science.chemistry.inorganic # Inorganic chemistry
science.chemistry.physical # Physical chemistry, kinetics
science.chemistry.biochem  # Biochemistry, enzymes

# Biology (6 domains)
science.biology            # General biology
science.biology.molecular  # DNA, RNA, gene expression
science.biology.cellular   # Cell biology, mitochondria
science.biology.genetics   # Genetics, CRISPR, evolution
science.biology.ecology    # Ecology, biodiversity
```

**Keywords**: riemann curvature, quantum mechanics, lagrangian, black hole, organic chemistry, dna, mitochondria, evolution

---

### 8. AI & Machine Learning (15 domains)

Deep learning, NLP, LLMs, RAG, embeddings, AI agents.

```
ai.core                    # Generic AI
ai.machine_learning        # ML, supervised/unsupervised learning
ai.deep_learning           # Neural networks, CNNs, RNNs, LSTMs
ai.nlp                     # Natural language processing, NER
ai.llm                     # Large language models (GPT, Claude, Gemini)
ai.transformers            # Transformers, attention mechanisms, BERT
ai.embeddings              # Vector embeddings, word2vec, semantic similarity
ai.rag                     # Retrieval-augmented generation, hybrid search
ai.agent                   # AI agents, tool use, chain of thought
ai.reinforcement           # Reinforcement learning, Q-learning
ai.computer_vision         # Computer vision, object detection, YOLO
ai.prompt_engineering      # Prompt engineering, few-shot learning
ai.training                # Model training, fine-tuning, transfer learning
ai.inference               # Inference optimization, quantization, ONNX
ai.ethics                  # AI ethics, alignment, bias, fairness
```

**Keywords**: machine learning, deep learning, llm, transformer, embedding, rag, ai agent, prompt engineering, ai ethics

---

### 9. Enterprise & Consulting (6 domains)

Enterprise architecture, digital transformation, cloud platforms.

```
enterprise.architecture    # TOGAF, solution architecture
enterprise.consulting      # Management consulting, agile delivery
enterprise.integration     # ESB, API gateway, microservices
enterprise.cloud           # AWS, Azure, GCP, Kubernetes
enterprise.digital_transformation # Digital strategy, innovation
enterprise.data            # Data warehouse, ETL, BI
ntt_data.projects          # NTT DATA client work
ntt_data.methodologies     # NTT DATA-specific methods
```

**Keywords**: togaf, enterprise architecture, digital transformation, aws, azure, kubernetes, ntt data

---

### 10. BMAD Method (5 domains)

BMAD methodology, workflows, agents, project management.

```
bmad.method                # BMAD methodology
bmad.workflows             # BMAD workflows (create-agent, create-workflow)
bmad.agents                # Expert/simple/module agent patterns
bmad.builder               # BMad Builder tooling
bmad.patterns              # Design patterns, best practices
project.epic               # Epics
project.story              # User stories
project.sprints            # Sprint planning, execution
project.retrospective      # Retrospectives
project.agile              # Agile methodologies
```

**Keywords**: bmad, epic, user story, sprint, retrospective, agent pattern

---

### 11. GenerativeDrive Energy Project (Tags, not domains)

**Note**: GD uses **tags** (not primary domains) for granular context:

```python
GD_KEYWORD_TAGS = {
    "sines", "hydrogen", "hydrogen_green", "solar", "wind", "hydro",
    "smart_grid", "water_loops", "plastics", "renewable_energy", "ai"
}
```

Primary domains for GD content are determined by context:
- `gd.generative_drive` (via path heuristics: `docs/gd-*`, `GenerativeDrive*`)
- `economics.energy` (energy economics)
- `project.*` (GD project docs)

---

### 12. Development & Infrastructure (24 domains)

Frameworks, containers, databases, CI/CD.

```
# Development (10 domains)
dev.spring_boot            # Spring Boot, Spring Framework
dev.python                 # Django, Flask, FastAPI
dev.frontend               # React, Vue, Angular
dev.nodejs                 # Node.js
dev.java                   # Java
dev.javascript             # JavaScript
dev.typescript             # TypeScript
dev.go                     # Golang
dev.rust                   # Rust
dev.cpp                    # C++

# Infrastructure (14 domains)
infra.docker               # Docker, Docker Compose
infra.kubernetes           # Kubernetes, Helm, K8s
infra.postgres             # PostgreSQL
infra.sql                  # MySQL, MariaDB, SQLite
infra.nosql                # MongoDB, Cassandra
infra.redis                # Redis
infra.qdrant               # Qdrant vector DB
infra.vector_db            # Pinecone, Weaviate, Milvus
infra.messaging            # Kafka, RabbitMQ, PubSub
infra.cicd                 # CI/CD, GitHub Actions, GitLab CI
infra.iac                  # Terraform, Ansible, IaC
infra.monitoring           # Prometheus, Grafana, Datadog, ELK
infra.webserver            # Nginx, Apache
infra.proxy                # HAProxy, Envoy, Traefik
```

**Keywords**: spring boot, docker, kubernetes, postgresql, qdrant, kafka, terraform, prometheus

---

## Heuristic Classification Flow

Domain cataloging in `domain_catalog._heuristic_metadata_from_payload()`:

1. **Direct domain mappings** (payload-level `domain` field)
2. **Source path heuristics** (folder structure: `docs/sprints/`, `.bmad/bmm/`, etc.)
3. **Title-based heuristics** (document titles containing "epic", "GD Sines", etc.)
4. **Section-based heuristics** (sections like "Architecture", "PRD")
5. **Text content heuristics** (`CHAVAO_DOMAIN_MAP` keyword matching - **881 mappings**)
6. **GD tag enrichment** (if GD-related, add `GD_KEYWORD_TAGS`)
7. **LLM fallback** (only if heuristics fail)

**Cost Optimization**: Heuristics-first approach reduces LLM calls by ~70% (measured in production).

---

## Validation

Run taxonomy validator:

```bash
python -m jarvis.memory.validate_domains
```

**Validation Rules**:
- Lowercase with underscores or dots only
- No leading/trailing dots or underscores
- Maximum 3 levels deep (e.g., `jarvis.memory.rag`)
- No keyword conflicts between `DIRECT_DOMAIN_MAP` and `CHAVAO_DOMAIN_MAP`

**Current Status**: ✅ **166 domains validated, 0 conflicts**

---

## Statistics

| Metric | Count |
|--------|-------|
| **Total unique domains** | 166 |
| **Total keyword mappings** | 881 |
| **Total direct mappings** | 5 |
| **Total GD tags** | 72 |
| **Top-level categories** | 17 |
| **Depth 2 domains** | 147 (88%) |
| **Depth 3 domains** | 19 (12%) |

**Coverage Expansion**: 50 → 881 keyword mappings (17.6x increase), 20 → 166 domains (8.3x increase)

---

## Maintenance Guidelines

### Adding New Domains

1. **Choose the correct submodule** under `heuristics/` based on discipline
2. **Add keyword mappings** to the appropriate `*_KEYWORD_MAP`
3. **Follow naming conventions**: lowercase, dots for hierarchy, max 3 levels
4. **Run validator**: `python -m jarvis.memory.validate_domains`
5. **Test**: Verify imports work and domain counts increase

### Domain Naming Conventions

```python
# Good examples
"jarvis.memory.rag"           # Clear hierarchy, 3 levels
"cyber.threat_intel"          # Lowercase, underscore for compound words
"science.physics.quantum"     # Maximum 3 levels

# Bad examples
"Jarvis.Memory"               # Use lowercase
"cyber_threat_intel"          # Use dots for hierarchy
"science.physics.quantum.qft" # Too deep (4 levels)
```

### When to Split a Category

Split when a top-level category exceeds **25 domains**. Example:

```python
# Before (24 domains under "network")
network.bgp
network.ospf
network.sdn
# ... 21 more

# After (split into network + telecom)
network.bgp              # Networking protocols
telecom.oss              # Carrier-grade systems
```

---

## Future Enhancements

1. **Hierarchical Querying**: Filter by top-level category (e.g., "show all `jarvis.*` domains")
2. **Domain Confidence Scoring**: Track heuristic match confidence
3. **Dynamic Domain Discovery**: Auto-suggest new domains based on ingestion patterns
4. **Domain Relationships**: Model cross-domain relationships (e.g., `jarvis.memory.rag` ↔ `ai.rag`)
5. **Domain Aliases**: Support alternate names (e.g., "Kubernetes" → `infra.kubernetes`, `k8s` → same)

---

## References

- **Implementation**: [src/jarvis/memory/heuristics/](../../src/jarvis/memory/heuristics/)
- **Validator**: [src/jarvis/memory/validate_domains.py](../../src/jarvis/memory/validate_domains.py)
- **Usage**: [domain_catalog.py](../../src/jarvis/memory/domain_catalog.py) lines 155-331
- **BMAD Method**: [.bmad/bmm/](../../.bmad/bmm/)
- **FirstResults**: [docs/archive/firstResults.md](../archive/firstResults.md) (real-world validation)
