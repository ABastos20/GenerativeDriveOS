import os
os.environ.setdefault('POSTGRES_HOST','postgres')
os.environ.setdefault('POSTGRES_PORT','5432')
os.environ.setdefault('POSTGRES_DB','jarvis')
os.environ.setdefault('POSTGRES_USER','jarvis')
os.environ.setdefault('POSTGRES_PASSWORD','jarvis-dev-password')

import importlib
mod = importlib.import_module('jarvis.database.postgres')
print('before cached:', getattr(mod, '_pgcrypto_available', None))
try:
    eng = mod.get_engine()
    print('engine created')
except Exception as e:
    print('engine error:', e)
print('after cached:', getattr(mod, '_pgcrypto_available', None))
print('is_pgcrypto_available():', mod.is_pgcrypto_available())
