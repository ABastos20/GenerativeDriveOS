import os
os.environ.setdefault('POSTGRES_HOST','postgres')
os.environ.setdefault('POSTGRES_PORT','5432')
os.environ.setdefault('POSTGRES_DB','jarvis')
os.environ.setdefault('POSTGRES_USER','jarvis')
os.environ.setdefault('POSTGRES_PASSWORD','jarvis-dev-password')

from psycopg import connect

try:
    with connect(host=os.environ['POSTGRES_HOST'], user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'], dbname=os.environ['POSTGRES_DB']) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname='pgcrypto';")
            r = cur.fetchone()
            print('pg_extension row:', r)
except Exception as e:
    print('connect error:', e)
