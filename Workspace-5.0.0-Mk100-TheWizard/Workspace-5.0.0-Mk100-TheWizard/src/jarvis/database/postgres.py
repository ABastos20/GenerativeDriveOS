"""PostgreSQL database connection and session management.

This module provides:
- SQLAlchemy engine with connection pooling
- Session factory and context manager
- Custom exception classes
- Environment-based configuration

Connection pooling is configured per architecture.md:
- Pool size: 5 connections
- Max overflow: 10 connections
- Pool pre-ping: enabled (test connections before use)
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

LOGGER = logging.getLogger(__name__)


# --- Custom Exceptions -----------------------------------------------------------


class DatabaseError(Exception):
    """Base exception for database operations."""


class ConnectionError(DatabaseError):
    """Database connection failed."""


class SessionError(DatabaseError):
    """Database session management failed."""


# --- Configuration ---------------------------------------------------------------


def get_connection_string() -> str:
    """Build PostgreSQL connection string from environment variables.

    Environment variables:
        POSTGRES_HOST: Database host (default: postgres)
        POSTGRES_PORT: Database port (default: 5432)
        POSTGRES_DB: Database name (default: jarvis)
        POSTGRES_USER: Database user (default: jarvis)
        POSTGRES_PASSWORD: Database password (required)

    Returns:
        PostgreSQL connection string in SQLAlchemy format

    Raises:
        ConnectionError: If required environment variables are missing
    """
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    database = os.environ.get("POSTGRES_DB", "jarvis")
    user = os.environ.get("POSTGRES_USER", "jarvis")
    password = os.environ.get("POSTGRES_PASSWORD")

    if not password:
        raise ConnectionError(
            "POSTGRES_PASSWORD environment variable is required. "
            "Set it in .env file or export it in your shell."
        )

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


# --- Engine & Session Factory ----------------------------------------------------


_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None
_pgcrypto_available: Optional[bool] = None


def get_engine(pool_size: int = 5, max_overflow: int = 10, echo: bool = False) -> Engine:
    """Get or create SQLAlchemy engine with connection pooling.

    Args:
        pool_size: Number of connections to maintain in pool (default: 5)
        max_overflow: Maximum overflow connections beyond pool_size (default: 10)
        echo: Echo SQL queries to stdout for debugging (default: False)

    Returns:
        SQLAlchemy engine instance

    Raises:
        ConnectionError: If engine creation fails
    """
    global _engine, _pgcrypto_available

    if _engine is not None:
        return _engine

    try:
        connection_string = get_connection_string()

        # Configure connection pooling (architecture.md: 5-10 connections)
        # Configure connection pooling (architecture.md: 5-10 connections)
        _engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before using them
            echo=echo,
            future=True,  # Use SQLAlchemy 2.0 style
        )

        # Observability: Instrument SQLAlchemy engine if OTel libraries are present
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            SQLAlchemyInstrumentor().instrument(engine=_engine)
            LOGGER.debug("SQLAlchemy instrumented with OpenTelemetry")
        except ImportError:
            pass


        LOGGER.info(
            "Database engine created",
            extra={
                "host": os.environ.get("POSTGRES_HOST", "postgres"),
                "database": os.environ.get("POSTGRES_DB", "jarvis"),
                "pool_size": pool_size,
                "max_overflow": max_overflow,
            },
        )

        # Try to enable/check pgcrypto for gen_random_uuid() support.
        # This is best-effort: many managed DBs won't allow CREATE EXTENSION;
        # we catch permission errors and fall back to Python UUID generation.
        try:
            with _engine.connect() as conn:
                try:
                    # Use exec_driver_sql to run raw SQL via the DBAPI driver
                    conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
                    _pgcrypto_available = True
                    LOGGER.info("pgcrypto extension is available/enabled")
                except DBAPIError:
                    # DB may refuse CREATE EXTENSION due to privileges; log and continue.
                    _pgcrypto_available = False
                    LOGGER.warning(
                        "Could not create pgcrypto extension (insufficient privileges?)",
                        exc_info=True,
                    )
        except SQLAlchemyError:
            # If the connection itself fails, leave availability unknown (None)
            _pgcrypto_available = False

        return _engine

    except SQLAlchemyError as e:
        raise ConnectionError(f"Failed to create database engine: {e}") from e


def get_session_factory() -> sessionmaker:
    """Get or create SQLAlchemy session factory.

    Returns:
        Session factory (sessionmaker instance)

    Raises:
        ConnectionError: If engine creation fails
    """
    global _SessionLocal

    if _SessionLocal is not None:
        return _SessionLocal

    engine = get_engine()
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic cleanup.

    Usage:
        with get_session() as session:
            conversation = session.query(Conversation).first()
            # ... work with session

    Yields:
        SQLAlchemy session

    Raises:
        SessionError: If session creation fails
        DatabaseError: If database operations fail
    """
    SessionLocal = get_session_factory()

    session: Optional[Session] = None
    try:
        session = SessionLocal()
        yield session
        session.commit()
    except SQLAlchemyError as e:
        if session:
            session.rollback()
        LOGGER.error("Database session error", exc_info=True, extra={"error": str(e)})
        raise DatabaseError(f"Database operation failed: {e}") from e
    finally:
        if session:
            session.close()


def close_engine() -> None:
    """Close database engine and dispose of connection pool.

    Use this for graceful shutdown in tests or application teardown.
    """
    global _engine, _SessionLocal

    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
        LOGGER.info("Database engine closed and connection pool disposed")


# --- Testing Support -------------------------------------------------------------


def get_test_engine(database_url: Optional[str] = None) -> Engine:
    """Create a test engine with NullPool (no connection pooling).

    Args:
        database_url: Optional test database URL (defaults to env config)

    Returns:
        SQLAlchemy engine for testing
    """
    url = database_url or get_connection_string()

    return create_engine(
        url,
        poolclass=NullPool,  # No pooling for tests (fresh connection each time)
        echo=False,
        future=True,
    )


def is_pgcrypto_available() -> bool:
    """Return whether pgcrypto appears available on the connected database.

    This reads a cached value if we've already attempted to detect/enable the
    extension. If no engine has been created yet, it will attempt a lightweight
    check by creating a temporary engine.
    """
    global _pgcrypto_available

    # If we've already confirmed availability, keep returning True.
    if _pgcrypto_available:
        return True

    try:
        engine = _engine or get_engine()
        with engine.connect() as conn:
            result = conn.exec_driver_sql("SELECT 1 FROM pg_extension WHERE extname='pgcrypto';")
            row = result.fetchone()
            _pgcrypto_available = bool(row)
            return _pgcrypto_available
    except Exception:
        # Any error (connection, permissions, missing env) should result in False
        _pgcrypto_available = False
        return False
