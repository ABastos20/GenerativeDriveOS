"""FastAPI application entry point for JARVIS System.

This module creates and configures the FastAPI application instance,
registers routers, and provides middleware configuration.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, ORJSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from jarvis.api.chat import router as chat_router
from jarvis.api.conversations import router as conversations_router
from src.jarvis.api import memory as memory_module
from jarvis.api.dashboard import router as dashboard_router
from jarvis.api.trace import router as trace_router  # Story 4.5.6
from jarvis.api.docs import router as docs_router  # Story 4-9
from jarvis.api.governance import router as governance_router  # Story 9-1
from jarvis.api.middleware import GovernanceMiddleware

# Paths for templates and static files
BASE_DIR = Path(__file__).resolve().parent.parent  # Points to src/jarvis
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"

# Create FastAPI application with orjson for 5-10x faster JSON responses
# Create FastAPI application with orjson for 5-10x faster JSON responses
app = FastAPI(
    title="JARVIS System API",
    description="Multi-agentic RAG system with persistent memory and cost-optimized LLM routing",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    default_response_class=ORJSONResponse,  # HIGH-PERFORMANCE: 5-10x faster JSON
)

# Initialize Observability (Story 8-6 Phase 3)
try:
    from prometheus_client import make_asgi_app
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from jarvis.observability import TelemetryManager

    # Setup Telemetry Provider (Jaeger + Prometheus)
    telemetry = TelemetryManager(service_name="jarvis-api")
    telemetry.setup()

    # Instrument FastAPI (exclude noisy endpoints)
    FastAPIInstrumentor.instrument_app(app, excluded_urls="/api/health,/metrics,/static")

    # Mount Prometheus Metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
except ImportError:
    pass  # Allow running without telemetry dependencies for minimal envs

# Mount static files
# Mount static files (Frontend)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount API static files (Cognitive Cockpit) - served from src/jarvis/frontend/static
frontend_static = Path(__file__).resolve().parent.parent / "frontend" / "static"
if frontend_static.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_static)), name="frontend_static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Configure middleware
app.add_middleware(GovernanceMiddleware)
from starlette.middleware.sessions import SessionMiddleware
import os
import secrets
# Use persistent secret or generate one. For dev, generation is fine but resets sessions on restart.
# FIX: Use constant secret for development to prevent session invalidation on reload
SESSION_SECRET = os.environ.get("JARVIS_SESSION_SECRET", "dev_secret_mandatory_for_persistence_12345")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, https_only=False, same_site="lax")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from jarvis.api.auth import router as auth_router
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(memory_module.router)
app.include_router(chat_router)
app.include_router(dashboard_router)
app.include_router(trace_router)  # Story 4.5.6
app.include_router(docs_router)  # Story 4-9
app.include_router(docs_router)  # Story 4-9
app.include_router(governance_router)  # Story 9-1: Political Governance
from jarvis.api import auth_debug
app.include_router(auth_debug.router)

@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy", "service": "jarvis-api"}


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    """Root endpoint info.

    Returns:
        API metadata and primary entrypoints
    """
    return {
        "service": "JARVIS System API",
        "docs": "/api/docs",
        "health": "/api/health",
        "chat_ui": "/chat",
    }


@app.get("/login", tags=["auth"], response_class=HTMLResponse)
async def login_page() -> str:
    """Login landing page - Required before accessing protected UI pages."""
    login_html = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "login.html"
    if login_html.exists():
        return login_html.read_text(encoding="utf-8")
    return "<h1>Login page not found</h1>"


from jarvis.database.postgres import get_session
from jarvis.governance.models import GovernanceUser

# Helper for UI Role Checks
def verify_ui_access(request: Request, allowed_roles: list[str]) -> bool:
    user_id = request.session.get("user_id")
    if not user_id:
        return False
        
    with get_session() as db:
        user = db.get(GovernanceUser, user_id)
        if not user:
            return False
            
        if user.platform_role == "admin":
            return True
            
        if user.platform_role in allowed_roles:
            return True
            
    return False

@app.get("/graph", tags=["visualization"], response_class=HTMLResponse)
async def graph_viewer(request: Request) -> Any:
    """Serve the Knowledge Graph visualization Cognitive Cockpit."""
    if not request.session.get("user"):
         return RedirectResponse(url="/login?returnUrl=/graph")
    
    # Platform Role Check: Observer or above
    # Matrix: /graph -> OBSERVER, USER, ADMIN
    if not verify_ui_access(request, ["observer", "user"]):
         return HTMLResponse(content="<h1>403 Forbidden</h1><p>Insufficient Platform Privileges (Required: Observer)</p>", status_code=403)

    graph_html = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "graph_viewer.html"
    if graph_html.exists():
        return graph_html.read_text(encoding="utf-8")
    return "<h1>Graph Viewer not found</h1>"

@app.get("/chat", include_in_schema=False, response_class=HTMLResponse)
def chat_ui(request: Request) -> Any:
    """Minimal OpenAI-style web UI for chatting with Jarvis."""
    if not request.session.get("user"):
         return RedirectResponse(url="/login?returnUrl=/chat")

    # Platform Role Check: User or above
    # Matrix: /chat -> USER, ADMIN (Observer BLOCKED)
    if not verify_ui_access(request, ["user"]):
        return HTMLResponse(content="<h1>403 Forbidden</h1><p>Insufficient Platform Privileges (Required: User)</p>", status_code=403)

    from fastapi import Request
    
    # Create minimal request object for template rendering
    class FakeRequest:
        def __init__(self):
            self.url = type('obj', (object,), {'scheme': 'http', 'netloc': 'localhost', 'path': '/chat'})()
    
    response = templates.TemplateResponse("chat.html", {"request": FakeRequest()})
    return response.body.decode('utf-8')

@app.get("/governance", tags=["governance"], response_class=HTMLResponse)
async def governance_ui(request: Request) -> Any:
    """Serve the Governance Dashboard - Constitutional AI Control Plane."""
    print(f"[GOVERNANCE] Session Check: {dict(request.session)}", flush=True)
    
    if not request.session.get("user"):
         print("[GOVERNANCE] No user in session. Redirecting to login.", flush=True)
         return RedirectResponse(url="/login?returnUrl=/governance")

    # Platform Role Check: Observer or above
    # Matrix: /governance (UI) -> OBSERVER, USER, ADMIN
    if not verify_ui_access(request, ["observer", "user"]):
        return HTMLResponse(content="<h1>403 Forbidden</h1><p>Insufficient Platform Privileges (Required: Observer)</p>", status_code=403)

    dashboard_html = Path(__file__).resolve().parent.parent / "frontend" / "templates" / "governance_dashboard.html"
    if dashboard_html.exists():
        return dashboard_html.read_text(encoding="utf-8")
    return "<h1>Governance Dashboard not found</h1>"

# Register WebSocket router for real-time governance events
try:
    from jarvis.api.governance_ws import router as governance_ws_router
    app.include_router(governance_ws_router)
except ImportError:
    pass  # WebSocket router optional


