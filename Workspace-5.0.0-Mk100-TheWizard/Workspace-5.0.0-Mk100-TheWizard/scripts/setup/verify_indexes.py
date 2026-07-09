"""Check PostgreSQL indexes and verify performance optimization coverage."""
import os
import psycopg2

# Connect to database
conn = psycopg2.connect(
    dbname=os.environ.get("POSTGRES_DB", "jarvis"),
    user=os.environ.get("POSTGRES_USER", "jarvis"),
    password=os.environ["POSTGRES_PASSWORD"],
    host=os.environ.get("POSTGRES_HOST", "postgres"),
    port=os.environ.get("POSTGRES_PORT", 5432),
)
cur = conn.cursor()

print("=" * 80)
print("POSTGRESQL INDEX VERIFICATION REPORT")
print("=" * 80)

# 1. List all custom indexes (idx_*)
print("\n1. CUSTOM INDEXES (idx_*):")
print("-" * 80)
cur.execute("""
    SELECT tablename, indexname, indexdef
    FROM pg_indexes
    WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
    ORDER BY tablename, indexname;
""")
indexes = cur.fetchall()
for table, index_name, indexdef in indexes:
    print(f"  ✅ {table:25s} | {index_name}")

print(f"\n  Total custom indexes: {len(indexes)}")

# 2. List all tables
print("\n2. ALL TABLES IN DATABASE:")
print("-" * 80)
cur.execute("""
    SELECT table_name, 
           pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    ORDER BY table_name;
""")
tables = cur.fetchall()
for table, size in tables:
    print(f"  {table:30s} | {size}")

# 3. Check index usage on documents table
print("\n3. DOCUMENTS TABLE - INDEX USAGE TEST:")
print("-" * 80)
cur.execute("""
    EXPLAIN (FORMAT TEXT)
    SELECT * FROM documents
    WHERE domain = 'test' AND created_at > NOW() - INTERVAL '7 days'
    ORDER BY created_at DESC
    LIMIT 10;
""")
explain = cur.fetchall()
for line in explain:
    print(f"  {line[0]}")

# 4. Check for missing indexes on high-cardinality columns
print("\n4. HIGH-CARDINALITY COLUMNS (candidates for indexes):")
print("-" * 80)
cur.execute("""
    SELECT
        schemaname,
        tablename,
        attname,
        n_distinct,
        correlation
    FROM pg_stats
    WHERE schemaname = 'public'
      AND tablename IN ('documents', 'temporal_chunks', 'research_logs', 'cognitive_traces', 'messages')
      AND n_distinct > 10
    ORDER BY tablename, ABS(n_distinct) DESC;
""")
stats = cur.fetchall()
for schema, table, column, n_distinct, correlation in stats:
    has_index = any(table == t and column in idx for t, idx, _ in indexes)
    status = "✅ INDEXED" if has_index else "⚠️  NO INDEX"
    print(f"  {status} | {table:20s} | {column:20s} | distinct: {n_distinct:6.0f}")

# 5. Check existing indexes on key tables
print("\n5. EXISTING INDEXES ON KEY TABLES:")
print("-" * 80)
for table in ['documents', 'temporal_chunks', 'research_logs', 'cognitive_traces', 'messages']:
    cur.execute(f"""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public' AND tablename = '{table}'
        ORDER BY indexname;
    """)
    table_indexes = cur.fetchall()
    if table_indexes:
        print(f"\n  {table}:")
        for idx_name, idx_def in table_indexes:
            print(f"    - {idx_name}")

# 6. Count rows in key tables
print("\n6. TABLE ROW COUNTS:")
print("-" * 80)
for table in ['documents', 'temporal_chunks', 'research_logs', 'cognitive_traces', 'messages']:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"  {table:30s} | {count:6d} rows")
    except Exception as e:
        print(f"  {table:30s} | ERROR: {e}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)

cur.close()
conn.close()
