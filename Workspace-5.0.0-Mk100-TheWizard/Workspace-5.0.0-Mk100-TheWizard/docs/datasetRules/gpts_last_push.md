1. Canonical retrieval modes & Qdrant filters
Let’s formalise the four modes in terms of payload filters so there’s zero ambiguity.
Assume Qdrant payload has:
{
  "domain": "story",
  "tags": ["epic_4", "arches"],
  "is_latest": true,
  "is_system": false,
  "jarvis_core": false,
  "priority": 0.7,
  "semantic_family": "story",
  "session_date": "2025-12-03T00:00:00",
  "story_date": "2025-11-29T00:00:00"
}

1.1 NORMAL (default QA, Vision mode)
Goal: No system leakage, no archive noise.
def build_filter_normal(domains, tags):
    must = []
    must_not = [
        # never show system plane
        models.FieldCondition(
            key="is_system", match=models.MatchValue(value=True)
        ),
        # avoid archive by default
        models.FieldCondition(
            key="semantic_family", match=models.MatchValue(value="archive")
        ),
    ]

    if domains:
        must.append(models.FieldCondition(
            key="domain", match=models.MatchAny(any=domains)
        ))
    if tags:
        must.append(models.FieldCondition(
            key="tags", match=models.MatchAny(any=tags)
        ))

    # still respect is_latest
    must.append(models.FieldCondition(
        key="is_latest", match=models.MatchValue(value=True)
    ))

    return models.Filter(must=must, must_not=must_not)

This keeps you in corpus plane, fresh only.

1.2 NORMAL + allow_stale (historical view)
Goal: Same as NORMAL, but allow archive or older versions when user explicitly asks for “original PRD / before epic 4 / old version”.
def build_filter_normal_allow_stale(domains, tags):
    must = []
    must_not = [
        models.FieldCondition(
            key="is_system", match=models.MatchValue(value=True)
        ),
        # notice: NO semantic_family != "archive" here
    ]

    if domains:
        must.append(models.FieldCondition(
            key="domain", match=models.MatchAny(any=domains)
        ))
    if tags:
        must.append(models.FieldCondition(
            key="tags", match=models.MatchAny(any=tags)
        ))

    # drop is_latest → opens archive + stale versions
    return models.Filter(must=must, must_not=must_not)

Router heuristic to turn this on:


Query contains tokens like ("original", "first", "early", "before epic", "old prd").


Or explicit: include:archive, allow_stale, etc.



1.3 META (introspection / system plane)
Goal: Let Jarvis talk about himself; allow jarvis-core but avoid it in “normal infra” questions.
def build_filter_meta(domains, tags, include_system_docs=True):
    must = []
    must_not = []

    # key bit: optionally allow system plane
    if not include_system_docs:
        must_not.append(models.FieldCondition(
            key="is_system", match=models.MatchValue(value=True)
        ))

    if domains:
        must.append(models.FieldCondition(
            key="domain", match=models.MatchAny(any=domains)
        ))
    else:
        # META default: bias towards core+arch+epic+story
        must.append(models.FieldCondition(
            key="domain",
            match=models.MatchAny(any=[
                "jarvis-core", "architecture", "epic", "story"
            ])
        ))

    # META can still respect is_latest unless user also asked for historical
    must.append(models.FieldCondition(
        key="is_latest", match=models.MatchValue(value=True)
    ))

    return models.Filter(must=must, must_not=must_not)

Router heuristic:


Query matches (jarvis|your memory|your architecture|arches|cognitive trace|council of ricks|epic|sprint|story)


And does not clearly talk about GD/hydrogen/finance/etc.



1.4 TIME_SLICE (temporal navigation)
Two flavours: point date and range.
a) Point date – “what happened on 2025-12-03?”
def build_filter_time_slice_point(date_str: str):
    must = [
        models.FieldCondition(
            key="semantic_family",
            match=models.MatchAny(any=["session-log", "epic", "story"])
        ),
        models.FieldCondition(
            key="session_date",
            match=models.MatchValue(value=date_str)  # "2025-12-03"
        )
    ]
    must_not = [
        models.FieldCondition(
            key="is_system", match=models.MatchValue(value=True)
        )
    ]
    return models.Filter(must=must, must_not=must_not)

If you want to be more flexible you can:


Prefer sessions for point date


Fall back to stories/epics if nothing found


b) Range – “between Dec 2 and Dec 5”
def build_filter_time_slice_range(start: str, end: str):
    must = [
        models.FieldCondition(
            key="semantic_family",
            match=models.MatchAny(any=["session-log", "epic", "story"])
        ),
        models.Range(
            key="session_date",
            gte=start,   # "2025-12-02"
            lte=end,     # "2025-12-05"
        )
    ]
    must_not = [
        models.FieldCondition(
            key="is_system", match=models.MatchValue(value=True)
        )
    ]
    return models.Filter(must=must, must_not=must_not)

Controller logic (pseudocode):
mode = "NORMAL"
allow_stale = False
include_system_docs = False

if query_has_explicit_date(query):
    mode = "TIME_SLICE"
elif is_meta_question(query):
    mode = "META"
    include_system_docs = True
elif is_historical_question(query):
    allow_stale = True

# Then choose filter builder based on mode + flags

That’s your magic switchboard between “memory as a diary” and “memory as a knowledge base”.

2. Micro-stories shaped cleanly (so you can check Claude)
You already named them; this is the sanity spec:
Story 4-10 – Temporal Retrieval & Time-Slice Mode
ACs:


session_date written into payload for all docs/sessions/*.


Controller detects explicit dates (YYYY-MM-DD, “week of”, “in November 2025”).


TIME_SLICE mode uses semantic_family ∈ {"session-log","epic","story"}.


At least 2 unit tests:


“what happened on 2025-12-03” → only sessions with that date.


“what changed in Epic 4.5 between Dec 2 and Dec 5” → epics/stories in that range.




Story 4-11 – Session & Archive Ingestion Integrity
ACs:


jarvis admin dataset-audit (or equivalent CLI) prints:


count by semantic_family


count by domain




0 docs/sessions/*.md missing from audit.


0 docs/archive/*.md missing from semantic_family="archive".


Dry-run + real-run supported for ingest_workspace_docs.py.


Story 4-12 – Meta & Historical Toggles in UI
ACs:


UI exposes:


Include system docs (META plane)


Include historical docs (allow_stale)




Domain selector shows jarvis-core once ingested.


domain:jarvis-core prefix in query pipeline maps to:


domains=["jarvis-core"]


include_system_docs=True.





3. Extra “magic” ideas that cost little, pay a lot
Since you explicitly invited sparks:
3.1 Confidence + mode interaction
You already have:


trace.confidence_estimate


trace.severity (normal, low_confidence, etc.)


Use it to auto-escalate:


If mode=NORMAL and confidence_estimate < 0.3:


Auto-run a META/TIME_SLICE follow-up:


“Here is the answer (low confidence). I can also show you which documents and sessions are related to this topic. Do you want that?”






No new infra, just reuse cognitive trace + planner.

3.2 “Episode timeline” answers
For queries like:

“What did we do that week?”
“How did epic 4.5 progress over time?”

Use TIME_SLICE on sessions + epics, but render as a human timeline:


Date header


Session title + 1–2 bullets


Link to story/epic if present


It turns the temporal axis into a narrative, not just a list of chunks.

Net-net: you and Claude are right on the edge of full Vision mode:


Planes and semantic families: ✅


ARCHES spine and feedback loops: ✅


Ingestion rules: ✅


What’s left is exactly this:


Time axis


Explicit modes


UI switches




You’ve already got the Mark 42 flying; this bit is just bolting on the HUD calendar + black box viewer.

1. Shape the ingest_file API once, then forget about it
I’d make ingest_file the only public entrypoint for memory ingestion and give it the full Jarvis payload contract:
# src/jarvis/memory/ingest.py

def ingest_file(
    path: Path,
    *,
    domain: str,
    tags: list[str] | None = None,
    meta: dict | None = None,
    # keep old knobs so old CLI doesn’t break:
    source: str | None = None,
    force_domain: str | None = None,
    # …whatever you already had
) -> None:
    """
    Ingest a single file into Jarvis memory.

    - `domain`: canonical domain (architecture, jarvis-core, story, ...)
    - `tags`: high-level semantic tags
    - `meta`: extra payload (is_system, jarvis_core, is_latest, priority, semantic_family, dates, etc.)
    """

Key points:


Use keyword-only for new args (*, domain, tags, meta) so positional legacy calls don’t accidentally shift.


Keep all old parameters, but make them secondary / deprecated – new ingest paths should always go through (domain, tags, meta).


Inside:
    payload: dict = {}

    # 1) Base fields from old behaviour (if any)
    payload["domain"] = domain

    if tags:
        payload["tags"] = tags

    if meta:
        # meta wins over defaults, but we can enforce some invariants
        payload.update(meta)

    # Guardrails:
    payload.setdefault("is_latest", True)
    payload.setdefault("is_system", False)
    payload.setdefault("jarvis_core", False)
    payload.setdefault("priority", 0.5)
    payload.setdefault("semantic_family", "docs")

    # then call your existing lower-level helpers:
    #   - split into chunks
    #   - qdrant_client.upsert(..., payload=payload)
    #   - write Document row in Postgres with matching fields

So ingest_workspace_docs.py just does:
domain, tags, meta = classify(path)
ingest_file(path, domain=domain, tags=tags, meta=meta)

No weird kwargs, no custom variants.

2. Make sure payload + DB stay in sync
You’ve now got:


Qdrant payload fields: domain, tags, is_latest, is_system, jarvis_core, priority, semantic_family, session_date, etc.


Postgres documents table with at least: doc_key, version, is_latest, maybe domain.


When Claude changes ingest_file to accept tags/meta, the important bit is:


Whatever we store in Qdrant must be reconstructible from DB if we re-index.


The fields that matter for filters (is_system, is_latest, semantic_family, domain) should be part of the DB model, not only payload.


So for each ingest:


Upsert Document row:


domain


is_latest


is_system


semantic_family


priority (even if just a float column)




When chunking, push the same fields into payload.


That way a later “full reindex” can just read DB and rebuild Qdrant consistently.

3. Backwards compatibility checklist
When he changes the signature, this is what you want to validate:


Search for all ingest_file callers:


CLI scripts (scripts/ingest_jarvis_docs.py, old PoCs, etc.)


Any tests calling it directly.




For every caller:


New path (workspace classifier): ingest_file(path, domain=..., tags=..., meta=...).


Old path (legacy CLI): still valid because:


domain remains required.


New args are keyword-only and optional.






Add a tiny unit test in tests/unit/memory/test_ingest_file.py:


def test_ingest_file_accepts_tags_and_meta(tmp_path, fake_qdrant, db_session):
    path = tmp_path / "foo.md"
    path.write_text("# Hello")

    ingest_file(
        path,
        domain="jarvis-core",
        tags=["jarvis", "core"],
        meta={"is_system": True, "semantic_family": "core-memory"},
    )

    # Assert Document row has those attributes
    doc = db_session.query(Document).filter_by(path=str(path)).one()
    assert doc.domain == "jarvis-core"
    assert doc.is_system is True
    assert doc.semantic_family == "core-memory"

You don’t even need full Qdrant for that; can mock or stub.

4. Tiny safety invariant worth encoding
Now that ingest_file is the gate, encode the Vision rule there:

“System plane must always declare itself.”

Inside ingest_file:
if payload.get("is_system"):
    payload.setdefault("semantic_family", "core-memory")
    payload.setdefault("jarvis_core", True)

So even if one caller forgets to include semantic_family when is_system=True, you never silently create a “half-system” document.
That’s the kind of thing that prevents Ultron-style drift in six months when you’ve forgotten half these details.

Bottom line: Claude spotted exactly the right thing (ingest_file being too “thin”).
If he:


widens the signature as above,


merges tags/meta into payload + DB,


and you keep ingest_workspace_docs.py as the only high-level dispatcher,


you’ve got a single choke point where all dataset rules are enforced – which is exactly what you want at this stage.
Yeah, this is exactly the stage where the suit is basically all there, but a few plates are still misaligned and some old junk is still welded to the chassis.



### COre ARCHITECT NOTES!!!! Nuke the current environment let's start fresh we had nothing to begin with, but prepare pipelines crons everything
"""


1. Biggest real gap: old chunks without is_system (and friends)

Claude already spotted the core bug:

is_system filter ⚠️ Old chunks lack is_system field

Right now Qdrant has a mixed population:

New workspace docs → payload has
domain, tags, is_system, semantic_family, priority, etc.

Old chunks (from previous generations) → no is_system, maybe no semantic_family.

That means:

Filters like must_not(is_system == true) are not sufficient because:

Docs without is_system do not match is_system=true, so they slip through into NORMAL mode, even if they are effectively “system-ish”.

You have two realistic options:

1.1 Hard reset for internal indexes (recommended for your stage)

For Jarvis internal brain, it’s acceptable to:

Drop the old Qdrant collections (or at least the internal one).

Re-run:

cd Workspace
python scripts/ingest_workspace_docs.py


Optionally run your other ingest pipelines (GD playbooks, etc.) through the new ingest_file(path, domain=..., tags=..., meta=...) API.

This guarantees: every payload carries your canonical schema.

If you go this way, add a tiny “migration note” to dataSetRules.md:

v1 → pre-is_system; v2 → is_system + semantic_family mandatory.

1.2 If you don’t want to drop: targeted backfill

If wiping is inconvenient, do a payload backfill for old points:

For every payload without is_system:

If you can derive from doc_key/domain that it’s core → is_system=true, semantic_family="core-memory"

Else → is_system=false, semantic_family="docs" (or best-effort family)

But frankly, given where you are, a controlled “nuke & rebuild internal indexes” is simpler and safer.

2. RetrievalMode wiring: make ARCHES actually use it (Story 4-10)

Claude has:

RetrievalMode = NORMAL | META | TIME_SLICE | HISTORICAL

detect_retrieval_mode(query)

parse_date_from_query(query)

_build_filter_for_mode(...)

What’s missing is where this gets invoked in the controller.

2.1 Where to plug it

In ARCHESController (whatever method is orchestrating a query, e.g. handle_query()):

from jarvis.memory.search import RetrievalMode, detect_retrieval_mode

def handle_query(self, query: str, *, explicit_mode: RetrievalMode | None = None, **kwargs):
    # 1. Determine mode (explicit UI overrides auto)
    auto_mode = detect_retrieval_mode(query)
    mode = explicit_mode or auto_mode

    # 2. Derive flags for search
    include_system_docs = mode in {RetrievalMode.META}
    include_stale = mode in {RetrievalMode.HISTORICAL}
    time_slice = None

    if mode is RetrievalMode.TIME_SLICE:
        time_slice = parse_date_from_query(query)  # Claude already implemented
    # 3. Call search with mode-aware options
    results = search_memory(
        query=query,
        mode=mode,
        include_system_docs=include_system_docs,
        include_stale=include_stale,
        time_slice=time_slice,
        # plus domains/tags from UI
    )


And in search_memory(...) you route to _build_filter_for_mode.

2.2 Precedence rule (important)

Manual UI toggles (include_system_docs, allow_stale) MUST override detect_retrieval_mode.

Auto-mode is a hint, not a law.

So if user explicitly switches “Historical” in UI, you set:

explicit_mode = RetrievalMode.HISTORICAL


and skip the auto detection.

3. Temporal navigation: getting TIME_SLICE to actually cut on dates (Story 4-11)

Claude already added TIME_SLICE and parse_date_from_query. The missing pieces are:

Ingestion: every docs/sessions/*.md must carry session_date (you already spec’d this).

Filter: _build_filter_for_mode must add a payload date filter when mode=TIME_SLICE.

3.1 Ingestion: session_date

In classify(path) (ingest script):

You’re already doing something like:

if parts[0] == "sessions":
    semantic_family = "session-log"
    # parse YYYY-MM-DD from filename
    date = datetime.strptime(..., "%Y-%m-%d")
    meta["session_date"] = date.date().isoformat()


Just confirm:

It’s always written.

It ends up in the payload via meta.

3.2 Filters for TIME_SLICE

In _build_filter_for_mode(mode, time_slice, include_stale, include_system_docs, ...):

For exact day (e.g. 2025-12-03):

if mode is RetrievalMode.TIME_SLICE and time_slice is not None:
    filters.must.append(
        models.FieldCondition(
            key="session_date",
            match=models.MatchValue(value=time_slice.date().isoformat())
        )
    )
    # and probably semantic_family in session-log / epic / story


For “that week/month” you can later extend to ranges.

The key is: TIME_SLICE must actually narrow the payload; right now it sounds like the mode exists but the filter isn’t fully using the date.

4. Historical queries: HISTORICAL + allow_stale (Story 4-12 backend piece)

For HISTORICAL:

Rule: drop is_latest=true filter OR invert it to “include archive”.

Pseudo in _build_filter_for_mode:

if mode is RetrievalMode.NORMAL:
    filters.must.append(FieldCondition(key="is_latest", match=MatchValue(True)))
    filters.must_not.append(FieldCondition(key="is_system", match=MatchValue(True)))

elif mode is RetrievalMode.HISTORICAL:
    # do NOT add is_latest filter
    # optionally: prefer archive + older versions
    pass


And for allow_stale UI toggle, just set mode = HISTORICAL explicitly.

5. UI: surfaces to make Vision Mode visible (Story 4-12 frontend)

Once ingestion + filters are correct, the UI just needs to surface the knobs:

Domain selector:

Ensure /api/memory/domains/metadata now returns jarvis-core.

Show jarvis-core in the domain list.

Mark it visually as ⚠️ “System / Introspection” if you want.

Toggles:

Include system docs → maps to include_system_docs=True / mode=META.

Include historical docs → maps to allow_stale=True / mode=HISTORICAL.

Time-slice:

You can do it purely by NLP (date in query).

Optional: a date picker that sets mode=TIME_SLICE and passes a time_slice field directly (stronger than auto).

6. Extra “magic” I’d add now (small, high impact)

Two small touches that compound hard later:

6.1 Store retrieval_mode in CognitiveTrace

In CognitiveTrace dataclass:

retrieval_mode: Optional[str] = None  # "normal" | "meta" | "time_slice" | "historical"


Set it in ARCHESController before calling search:

trace.retrieval_mode = mode.value


This gives you:

Full audit: “this bad answer happened in HISTORICAL mode”.

Future analytics over how often META/HISTORICAL/TIME_SLICE are used.

6.2 Minimal tests for mode → filter contract

A single unit test file, tests/unit/memory/test_retrieval_modes.py:

NORMAL: filter includes is_latest=true, must_not is_system=true.

META: does not include must_not is_system, might not include is_latest=true.

TIME_SLICE: if time_slice=2025-12-03, filter has session_date == "2025-12-03".

HISTORICAL: no is_latest constraint.

Those 4 tests lock the semantics in place.

7. Where you stand

Given Claude’s report + your rules:

✅ Semantic families: done and correct.

✅ RetrievalMode enum + helpers: done.

✅ ingest_file expanded: done, needs to be your canonical gate from now on.

⚠️ Old chunks: still dirty, causing system leakage + inconsistent behaviour.

⚠️ Mode wiring: infra is there, ARCHES still not fully driving it.

⚠️ Temporal / historical UI: toggles and proper date filters still pending.

You’re genuinely one or two focused passes away from:

“Jarvis can answer:
– what I did on 2025-12-03
– what the original PRD was before Epic 4
– how his memory core is structured
without leaking or hallucinating internal specs in normal QA.”

Which is exactly the Vision vs Ultron line you defined.

If you want, next step I can sketch a single canonical _build_filter_for_mode(...) layout (all branches in one place) so you and Claude can just diff it against what’s in search.py and patch where needed.

"""