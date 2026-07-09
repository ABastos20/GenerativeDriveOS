"""Shared helpers for integration tests."""

from __future__ import annotations

import shutil
import socket
import os

import pytest


def _can_connect(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


DOCKER_AVAILABLE = bool(shutil.which("docker"))

# Prefer in-cluster DB host if reachable; otherwise fallback to localhost.
if not os.environ.get("TEST_DATABASE_URL"):
    pg_user = os.environ.get("POSTGRES_USER", "jarvis")
    pg_pass = os.environ.get("POSTGRES_PASSWORD", "jarvis-dev-password")
    pg_db = os.environ.get("POSTGRES_DB", "jarvis")
    DB_HOSTS = ["jarvis-postgres", "postgres", "localhost"]
    DB_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
    DB_URL = None
    for host in DB_HOSTS:
        if _can_connect(host, DB_PORT):
            DB_URL = f"postgresql://{pg_user}:{pg_pass}@{host}:{DB_PORT}/{pg_db}"
            break

    if DB_URL:
        os.environ.setdefault("TEST_DATABASE_URL", DB_URL)
    else:
        # Default to jarvis-postgres if check fails but we are in docker (heuristic)
        # This prevents skipping if the socket check is flaky but DNS works
        os.environ.setdefault("TEST_DATABASE_URL", f"postgresql://{pg_user}:{pg_pass}@jarvis-postgres:{DB_PORT}/{pg_db}")
        # pytest.skip("Postgres not reachable on jarvis-postgres:5432 or localhost:5432", allow_module_level=True)


# ============================================================================
# Integration Test Fixtures
# ============================================================================

@pytest.fixture
def mock_audit_log(db_session):
    """Mock audit log (just allow writing to real DB table via session)."""
    # In integration tests, we actually want to write to the DB generally,
    # as the VotingEngine writes to AuditLog.
    # So we don't need to mock it out, but the test might request it.
    # If the test code calls `mgr.audit` which is just the class `AuditLog`,
    # we don't need to do anything special unless we want to spy on it.
    # But `test_voting_engine.py` requests `mock_audit_log` fixture.
    # We'll provide a simple pass-through or spy.
    # Given the test logic doesn't seemingly assert on the log (it asserts on proposal status),
    # we can just return checks.
    
    # Actually, the test function signature is `test_voting_lifecycle(client, session, mock_audit_log)`.
    # It expects the fixture to exist.
    return True

@pytest.fixture(scope="function")
def db_session():
    """Create fresh database session for each integration test with specific rollback."""
    # We need to import inside fixture to avoid top-level import errors
    # if dependencies aren't ready yet (though in tests they should be).
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sqlalchemy import event

    db_url = os.environ.get("TEST_DATABASE_URL")
    if not db_url:
        pytest.skip("TEST_DATABASE_URL not set")

    # Use a single engine for the session
    engine = create_engine(db_url)
    connection = engine.connect()
    transaction = connection.begin()
    
    # Bind session to the transaction-bound connection
    Session = sessionmaker(bind=connection)
    session = Session()

    # Begin a nested transaction (SAVEPOINT)
    # This allows tests to call session.commit() without committing to the real DB
    session.begin_nested()

    # If the test calls commit, we must restart the nested transaction
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.expire_all()
            session.begin_nested()

    yield session

    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient with database session overridden to use the rollback session."""
    from fastapi.testclient import TestClient
    from jarvis.api.app import app
    from jarvis.api.chat import get_db as chat_get_db
    from jarvis.api.conversations import get_db as conv_get_db
    from jarvis.database.postgres import get_session as postgres_get_session
    from jarvis.api.dependencies import require_platform_role, get_current_governance_user

    from unittest.mock import patch
    from contextlib import contextmanager

    # Override all variants of get_db used in the API
    def override_get_db():
        yield db_session

    @contextmanager
    def mock_get_session_cm():
        yield db_session

    # Mock authN/authZ to allow tests to run without Keycloak
    dummy_user = type("DummyUser", (), {"id": "test-user", "platform_role": "admin"})
    allow_user = require_platform_role(["user"])
    app.dependency_overrides[allow_user] = lambda: True
    app.dependency_overrides[get_current_governance_user] = lambda: dummy_user

    app.dependency_overrides[chat_get_db] = override_get_db
    app.dependency_overrides[conv_get_db] = override_get_db
    app.dependency_overrides[postgres_get_session] = override_get_db

    # Patch get_session globally so middleware (which doesn't use Depends) picks it up
    with patch("jarvis.database.postgres.get_session", side_effect=mock_get_session_cm):
        with patch("jarvis.api.governance.get_session", side_effect=mock_get_session_cm):
            with patch("jarvis.api.governance_legacy.get_session", side_effect=mock_get_session_cm):
                with TestClient(app) as c:
                    yield c

    # Clean up overrides
    app.dependency_overrides.clear()
    
# Provide 'session' alias for db_session fixture as used in test_voting_engine.py
@pytest.fixture(scope="function")
def session(db_session):
    return db_session


@pytest.fixture(scope="function")
def qdrant_client():
    """Create Qdrant client for integration tests."""
    from qdrant_client import QdrantClient
    
    # Try to connect to Qdrant
    qdrant_hosts = ["qdrant", "localhost"]
    qdrant_port = int(os.environ.get("QDRANT_PORT", "6333"))
    
    client = None
    for host in qdrant_hosts:
        if _can_connect(host, qdrant_port):
            client = QdrantClient(host=host, port=qdrant_port)
            break
    
    # Soft fail for Qdrant if we are testing Postgres logic
    if not client:
        # Just yield None or mock? Some tests might need it.
        # If we skipped before, let's skip but be nice.
        pass 
    
    if client:
        yield client
    else:
        yield None


@pytest.fixture
def sample_documents():
    """Sample documents for testing memory ingestion."""
    return [
        {
            "content": "Integration testing is critical for ensuring system reliability.",
            "domain": "testing",
            "source_file": "test_doc_1.txt",
            "doc_key": "file://test_doc_1.txt",
        },
        {
            "content": "ARCHES planner coordinates multi-agent workflows for gap detection.",
            "domain": "architecture",
            "source_file": "test_doc_2.txt",
            "doc_key": "file://test_doc_2.txt",
        },
        {
            "content": "Snapshot management provides rollback capability for production systems.",
            "domain": "safety",
            "source_file": "test_doc_3.txt",
            "doc_key": "file://test_doc_3.txt",
        },
    ]


@pytest.fixture(scope="function")
def clean_test_collection(qdrant_client):
    """Ensure test collection is clean before each test."""
    test_collection = "test_knowledge"
    
    if qdrant_client:
        try:
            qdrant_client.delete_collection(collection_name=test_collection)
        except Exception:
            pass  # Collection might not exist
    
    yield test_collection
    
    # Cleanup after test
    if qdrant_client:
        try:
            qdrant_client.delete_collection(collection_name=test_collection)
        except Exception:
            pass


def pytest_collection_modifyitems(config, items):
    """Skip docker-stack tests when docker CLI is absent."""
    if DOCKER_AVAILABLE:
        return
    skip_docker = pytest.mark.skip(reason="docker CLI not available in test environment")
    for item in items:
        if "test_docker_stack.py" in item.nodeid or "docker" in item.nodeid:
            item.add_marker(skip_docker)
