# Story 4.5.3b: Qdrant is_latest Payload Filter (Tech Debt)

Status: done

## Story

As a **Jarvis developer optimizing retrieval performance**,
I want **recency/lineage filtering to happen at Qdrant query time via `is_latest` payload field**,
so that **we don't over-fetch stale chunks as corpus scales beyond 1M chunks**.

## Acceptance Criteria

1. [ ] `is_latest` boolean field added to Qdrant chunk payloads
2. [ ] Ingest pipeline marks new versions as `is_latest=true` and old as `false`
3. [ ] Qdrant filter includes `is_latest=true` by default
4. [ ] `version` integer column added to documents table
5. [ ] Performance benchmarks show reduced retrieval latency at scale

## Priority

**Performance/Infra** - Not blocking. Implement when corpus hits ~500K chunks or latency increases.

## Notes

- Current approach (post-retrieval filtering) works fine for current scale
- This is the "proper" solution for long-term scalability
- Depends on ingest pipeline refactor

## References

- Story 4.5.3 implemented freshness scoring post-retrieval
- GPT analysis identified this as an optimization opportunity


## GPT NOTES

### 1. Story & ACs – small surgical upgrades
##################################################################################
Your story:

As a Jarvis developer optimizing retrieval performance,
I want recency/lineage filtering to happen at Qdrant query time via is_latest payload field,
so that we don't over-fetch stale chunks as corpus scales beyond 1M chunks.

Perfect. I’d add one nuance in the ACs:

Your current ACs

 is_latest boolean field added to Qdrant chunk payloads

 Ingest pipeline marks new versions as is_latest=true and old as false

 Qdrant filter includes is_latest=true by default

 version integer column added to documents table

 Performance benchmarks show reduced retrieval latency at scale

I’d extend with 2 more:

 Existing corpus backfilled: for each doc_key the freshest chunks are marked is_latest=true, older versions false

 --allow-stale (or equivalent historical mode) bypasses is_latest=true filter and/or uses a different Qdrant filter preset

Without (6) you’ll have mixed semantics until full re-ingest.
Without (7) you break your historical queries.

2. Implementation sketch (so 4.5.3b doesn’t blow up 4.5.3)
2.1. Schema changes

Postgres documents table

Add version INT NOT NULL DEFAULT 1

(Optional) Add is_latest BOOLEAN NOT NULL DEFAULT TRUE for querying from SQL.

Qdrant payload per chunk

Add:

"doc_key": "..." (already there)

"version": <int>

"is_latest": true | false

You can keep your current regex version resolution, but now you’ll have an explicit integer too.

2.2. Ingest pipeline behaviour

On ingest of a document with some doc_key:

Select existing doc row by doc_key:

If none: version = 1

If exists: version = existing.version + 1

Set all previous versions for that doc_key in DB to is_latest = false.

Insert or update the new doc row with is_latest = true, version = X.

For all chunks belonging to this ingest:

payload[doc_key] = doc_key

payload[version] = version

payload[is_latest] = true

(Optional enhancement / later):

Batch update Qdrant for old chunks: is_latest = false using a filter on doc_key and version < current.

For 4.5.3b, you can even skip step 5 initially if you rely strictly on version in Qdrant filter + “latest only” from DB, but the clean version is to keep Qdrant payload honest too.

2.3. Retrieval changes

Right now you:

Query Qdrant with filters (domain/tags/etc.)

Get top K

Apply freshness + conflict resolution post-retrieval

After 4.5.3b:

Default retrieval:

Add payload filter: is_latest == true

Historical mode (--allow-stale or “as of date X”):

Either:

remove is_latest filter

or use (is_latest == true OR version <= some cutoff)

Keep your post-retrieval freshness scoring – it still adds value even when old chunks are filtered out early (just weaker effect).

This way:

Qdrant drops stale versions early → less over-fetch.

Your existing 4.5.3 logic still works on top (no semantic change).

3. Benchmarks – enough to close AC 5

You don’t need a PhD perf lab, just something like:

Corpus:

baseline ~100k–200k chunks

synthetic bloat ~1M+ chunks (or extrapolate using repeated copies)

Two runs:

Before filter: same query set, no is_latest filter, same K.

After filter: same queries with is_latest=true filter.

Measure:

p50 / p90 latency of Qdrant query

size of result set returned by Qdrant (before local filtering)

CPU usage spikes on retrieval process (roughly)

As soon as you see:

less rows returned

lower or flat latency

→ AC 5 is satisfied.

4. Priority framing – fully agree

Performance/Infra – Not blocking. Implement when corpus hits ~500K chunks or latency increases.

Totally aligned.

Short-term: you’ve already fixed the behaviour in 4.5.3.
4.5.3b is about scaling comfort once Jarvis’s brain gets obese.

##################################################################################