from fastapi.testclient import TestClient
import importlib.util
import os

# Load the mcp_server module by file path to avoid package import issues
here = os.path.dirname(os.path.dirname(__file__))  # dev -> workspace
mcp_path = os.path.join(here, 'src', 'jarvis', 'mcp_server.py')
spec = importlib.util.spec_from_file_location('mcp_server', mcp_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

app = getattr(mod, 'app')
client = TestClient(app)

print('GET /mcp/ping')
r = client.get('/mcp/ping')
print(r.status_code, r.json())

print('GET /mcp/health')
r = client.get('/mcp/health')
print(r.status_code, r.json())
