1. Texto para mandares ao VS Code Claude (ingest + flags)

Ignora a parte antiga do ingest_workspace_docs.py onde estavas a usar apenas jarvis_core / introspection_only.

Passamos a seguir o que está no brainstorming “brainstorming-session-improve-ingestion-core-2025-12-05.md”:

- Novo campo obrigatório no payload: is_system: bool
- docs/jarvis/* (excepto playbooks) = cérebro de Jarvis:
  - domain = "jarvis-core"
  - jarvis_core = true
  - is_system = true
  - semantic_family = "core-memory"
  - priority = 1.0
- docs/jarvis/playbooks/*:
  - domain = "jarvis-playbooks"
  - jarvis_core = false
  - is_system = false
  - semantic_family = "playbook"
  - priority ~0.8

- docs/archive/*:
  - domain = "archive"
  - is_latest = false
  - is_system = false
  - expose_in_default_retrieval = false (ou priority muito baixa)

- Resto mantemos na mesma lógica que já tinhas: architecture, features, sessions, stories, epics, etc.
  - is_system = false por default.

Actualiza a função classify(path) para devolver sempre:
  - domain: str
  - tags: list[str]
  - meta: dict com pelo menos:
      - is_latest: bool
      - priority: float
      - jarvis_core: bool
      - is_system: bool
      - semantic_family: str

Usa este esqueleto como base (podes adaptar, mas mantém os campos e a semântica):

```python
def classify(path: pathlib.Path) -> tuple[str, list[str], dict]:
    rel = path.relative_to(BASE)
    parts = rel.parts

    domain = "docs"
    tags: list[str] = []
    meta: dict = {
        "is_latest": True,
        "priority": 0.5,
        "jarvis_core": False,
        "is_system": False,
        "semantic_family": "generic",
    }

    if parts[0] == "architecture":
        domain = "architecture"
        tags += ["architecture", "jarvis", "memory", "design"]
        meta["priority"] = 0.9
        meta["semantic_family"] = "architecture"
        # ... casos especiais (jarvis-memory-architecture.md, etc.)

    elif parts[0] == "archive":
        domain = "archive"
        tags += ["archive", "legacy", "historical", "old_blueprint"]
        meta["is_latest"] = False
        meta["priority"] = 0.2
        meta["semantic_family"] = "archive"

    elif parts[0] == "features":
        domain = "features"
        tags += ["features", "ui", "jarvis"]
        meta["priority"] = 0.75
        meta["semantic_family"] = "feature"

    elif parts[0] == "jarvis":
        # playbooks
        if len(parts) >= 2 and parts[1] == "playbooks":
            domain = "jarvis-playbooks"
            tags += ["jarvis", "playbook"]
            meta["priority"] = 0.8
            meta["jarvis_core"] = False
            meta["is_system"] = False
            meta["semantic_family"] = "playbook"
        else:
            # CORE ABSOLUTO
            domain = "jarvis-core"
            tags += ["jarvis", "core", "arches", "cognition", "memory"]
            meta["priority"] = 1.0
            meta["jarvis_core"] = True
            meta["is_system"] = True
            meta["semantic_family"] = "core-memory"
            # casos especiais por filename:
            if rel.name == "memory.core.md":
                tags += ["memory_core", "ontology", "priority_high"]
            elif rel.name == "operating-manual.md":
                tags += ["operating_manual", "ops"]
            elif rel.name == "persona.md":
                tags += ["personas", "council"]
            elif rel.name == "gd-overview.md":
                tags += ["generative_drive", "gd_core"]
            elif rel.name == "integration-plan.md":
                tags += ["integration", "roadmap"]

    elif parts[0] == "sessions":
        domain = "sessions"
        tags += ["session_log", "temporal", "jarvis_session"]
        meta["priority"] = 0.4
        meta["semantic_family"] = "session-log"
        # parse data do filename se possível

    elif parts[0] == "sprints":
        # stories vs epics/process, mesma lógica que já tinhas
        ...

    else:
        # root docs: architecture.md, jarvis-knowledge-pipeline.md, LLM_*, etc.
        ...

    base = rel.stem.replace(".", "_").replace(" ", "_").lower()
    tags.append(base)
    tags = sorted(set(tags))
    return domain, tags, meta


Mantém a lógica anterior de tags/domínios onde já está boa, só garante:

docs/jarvis/* → is_system = True (excepto playbooks)

tudo o resto → is_system = False

Depois disso, o ingest_file() continua igual, só passa meta["is_system"] no payload Qdrant.


---

## 2. Texto para mandares sobre o retrieval filter (`_build_qdrant_filter`)

Este é o segundo bloco que convém mandares logo a seguir:

```text
Actualiza também o lado de retrieval para respeitar is_system.

Na função _build_qdrant_filter (em search.py ou equivalente), precisamos de:

- Novo parâmetro: allow_system: bool = False
- Por default:
    - Filtrar is_latest = True (já temos via 4.5.3b)
    - Filtrar is_system = False  (não queremos cérebro no QA normal)
- Só quando:
    - domain inclui "jarvis-core"
    - OU modo/meta-intenção for introspecção
  → allow_system = True (e então NÃO filtramos is_system)

Algo do género:

```python
def _build_qdrant_filter(
    domains: list[str] | None,
    tags: list[str] | None,
    *,
    include_stale: bool = False,
    allow_system: bool = False,
) -> models.Filter:
    must: list[models.Condition] = []

    if not include_stale:
        must.append(models.FieldCondition(
            key="is_latest",
            match=models.MatchValue(value=True),
        ))

    # filtro novo: is_system
    if not allow_system:
        must.append(models.FieldCondition(
            key="is_system",
            match=models.MatchValue(value=False),
        ))

    if domains:
        must.append(models.FieldCondition(
            key="domain",
            match=models.MatchAny(any=domains),
        ))

    if tags:
        must.append(models.FieldCondition(
            key="tags",
            match=models.MatchAny(any=tags),
        ))

    return models.Filter(must=must)


Depois, na search_memory / chat flow:

Chat normal → allow_system=False

Perguntas de introspecção / arquitectura / "como é que TU funcionas?" → allow_system=True

Se o utilizador escolher explicitamente o domain "jarvis-core" no UI → allow_system=True.

Isto garante o que definimos na brainstorming session:

is_system = true vive no plano de sistema, não contamina o corpus normal

Só aparece quando pedimos introspecção/arquitectura.


---

## 3. Pequeno sanity-check depois do ingest

Depois de ele ajustar o script e antes de correres full ingest a sério, podes pedir:

```text
Antes de correres ingest a sério, faz um dry-run de 5–10 ficheiros de cada zona (jarvis-core, playbooks, archive, features, stories) e mostra-me os payloads (domain, tags, is_system, jarvis_core, semantic_family, priority).

Quero confirmar:
- docs/jarvis/memory.core.md → domain="jarvis-core", is_system=True, jarvis_core=True
- docs/jarvis/playbooks/* → domain="jarvis-playbooks", is_system=False
- docs/archive/* → is_latest=False, is_system=False
- uma story random → domain="story", is_system=False


Se esses quatro pontos baterem certo, estás com Vision bem separado do resto do MCU.