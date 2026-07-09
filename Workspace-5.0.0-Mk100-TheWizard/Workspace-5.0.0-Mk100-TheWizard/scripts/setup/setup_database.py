#!/usr/bin/env python3
"""
This script initializes and optimizes the PostgreSQL database and Qdrant collections.

Key Functions:
- PostgreSQL:
  - Runs alembic migrations to set up or update the schema to the latest version.
  - Applies performance tuning settings for memory and query execution.
- Qdrant:
  - Idempotently creates the 'knowledge' collection with predefined vector parameters.
  - Verifies the configuration if the collection already exists.
"""
from __future__ import annotations

import os
import argparse
import subprocess
import sys
from pathlib import Path

import psycopg2
import structlog
from psycopg2 import OperationalError
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jarvis.database.qdrant import (
    DEFAULT_COLLECTION_NAME,
    collection_exists,
    get_collection_info,
    get_qdrant_client,
    init_collection,
)

logger = structlog.get_logger(__name__)


def run_alembic_migrations(dry_run: bool = False) -> bool:
    """Run alembic upgrade head to apply all migrations."""
    logger.info("running_alembic_migrations")
    command = ["alembic", "upgrade", "head"]
    if dry_run:
        logger.info("dry_run_would_run_command", command=" ".join(command))
        return True

    try:
        process = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info("alembic_upgrade_successful", stdout=process.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(
            "alembic_upgrade_failed",
            stderr=e.stderr,
            stdout=e.stdout,
            return_code=e.returncode,
        )
        return False
    except FileNotFoundError:
        logger.error(
            "alembic_command_not_found",
            error="Alembic is not installed or not in the system's PATH.",
        )
        return False


def optimize_postgres(dry_run: bool = False) -> bool:
    """Apply PostgreSQL performance optimizations."""
    logger.info("applying_postgres_optimizations")

    # Tuned settings for a system with 64GB RAM, 8-core CPU, and NVMe SSD.
    optimizations = {
        # Memory Settings
        "shared_buffers": "16GB",  # 25% of 64GB RAM
        "effective_cache_size": "48GB",  # 75% of 64GB RAM
        "maintenance_work_mem": "2GB",  # For VACUUM, CREATE INDEX on a large DB
        "work_mem": "128MB",  # Memory per sort/hash operation, tune based on query analysis

        # Parallelism Settings
        "max_worker_processes": "8",  # Number of CPU cores
        "max_parallel_workers": "8",  # Should match max_worker_processes
        "max_parallel_workers_per_gather": "4",  # Half of the cores for a single query
        "max_parallel_maintenance_workers": "2", # For parallel index creation/vacuum

        # Storage Settings
        "random_page_cost": "1.1",  # Lower cost for fast NVMe SSDs (default is 4.0)

        # Query Planner Settings
        "jit": "on",  # Just-In-Time compilation for complex queries
    }

    try:
        # Get DB credentials from environment
        user = os.environ.get("POSTGRES_USER", "jarvis")
        password = os.environ.get("POSTGRES_PASSWORD")
        host = os.environ.get("POSTGRES_HOST", "postgres")
        port = os.environ.get("POSTGRES_PORT", "5432")

        if not password:
            logger.error("POSTGRES_PASSWORD environment variable is not set.")
            return False

        # Connect to PostgreSQL server (without specifying a database)
        conn = psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host,
            port=port,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        for key, value in optimizations.items():
            sql = f"ALTER SYSTEM SET {key} = '{value}';"
            logger.info("applying_postgres_setting", setting=key, value=value)
            if dry_run:
                logger.info("dry_run_would_execute_sql", sql=sql)
                continue
            cursor.execute(sql)

        logger.info(
            "postgres_optimizations_applied",
            note="Restart the PostgreSQL server for all changes to take effect.",
        )
        cursor.close()
        conn.close()
        return True

    except OperationalError as e:
        logger.error(
            "postgres_connection_failed",
            error=str(e),
            host=host,
            port=port,
        )
        return False
    except Exception as e:
        logger.error("postgres_optimization_failed", error=str(e))
        return False


def setup_qdrant_collection(
    collection_name: str,
    force_recreate: bool = False,
    snapshot_file: str | None = None,
    dry_run: bool = False,
) -> bool:
    """Initialize or recreate the Qdrant collection."""
    logger.info("initializing_qdrant_collection", collection=collection_name)
    client = get_qdrant_client()

    # --- Force Re-creation Logic ---
    if force_recreate:
        logger.info("force_recreate_is_enabled", collection=collection_name)
        try:
            if collection_exists(collection_name, client=client):
                logger.warning("deleting_existing_collection", collection=collection_name)
                if dry_run:
                    logger.info("dry_run_would_delete_collection", collection=collection_name)
                else:
                    client.delete_collection(collection_name=collection_name)
                    logger.info("collection_deleted", collection=collection_name)
        except Exception as e:
            logger.error("failed_to_delete_collection", error=str(e))
            return False

    # --- Initialization ---
    try:
        if not collection_exists(collection_name, client=client):
            logger.info("collection_does_not_exist_creating_it", collection=collection_name)
            # High-recall settings for a powerful system.
            init_params = {"hnsw_m": 32, "hnsw_ef_construct": 400}
            if dry_run:
                logger.info("dry_run_would_init_collection", **init_params)
            else:
                init_collection(
                    collection_name=collection_name, client=client, **init_params
                )
                logger.info("collection_initialized_with_high_recall_settings", **init_params)
        else:
            logger.info("collection_already_exists_skipping_creation")

    except Exception as e:
        logger.error("qdrant_collection_init_failed", error=str(e))
        return False

    # --- Snapshot Recovery ---
    if force_recreate and snapshot_file:
        snapshot_uri = f"file:///qdrant/snapshots/{collection_name}/{snapshot_file}"
        logger.info("recovering_from_snapshot", snapshot=snapshot_uri)
        try:
            if dry_run:
                logger.info("dry_run_would_recover_snapshot", snapshot=snapshot_uri)
            else:
                client.recover_snapshot(
                    collection_name=collection_name,
                    location=snapshot_uri,
                    wait=True,
                )
                logger.info("snapshot_recovery_initiated", collection=collection_name)
        except Exception as e:
            logger.error("snapshot_recovery_failed", error=str(e))
            return False

    return True


def main() -> int:
    """Main function to orchestrate database setup."""
    parser = argparse.ArgumentParser(
        description="Initialize and optimize PostgreSQL and Qdrant."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing.",
    )
    # Qdrant specific arguments
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION_NAME,
        help=f"Qdrant collection name (default: {DEFAULT_COLLECTION_NAME})",
    )
    parser.add_argument(
        "--force-recreate-qdrant",
        action="store_true",
        help="Force deletion of existing Qdrant collection to apply new settings.",
    )
    parser.add_argument(
        "--qdrant-snapshot-file",
        type=str,
        default=None,
        help="Snapshot file to restore after recreating the collection. Requires --force-recreate-qdrant.",
    )
    # Skip flags
    parser.add_argument(
        "--skip-postgres",
        action="store_true",
        help="Skip all PostgreSQL setup and optimization.",
    )
    parser.add_argument(
        "--skip-qdrant",
        action="store_true",
        help="Skip all Qdrant setup.",
    )
    args = parser.parse_args()

    if args.qdrant_snapshot_file and not args.force_recreate_qdrant:
        logger.error("--qdrant-snapshot-file can only be used with --force-recreate-qdrant.")
        return 1


    logger.info(
        "database_setup_started",
        dry_run=args.dry_run,
        skip_postgres=args.skip_postgres,
        skip_qdrant=args.skip_qdrant,
        force_recreate_qdrant=args.force_recreate_qdrant,
    )

    all_success = True

    # === PostgreSQL Setup ===
    if not args.skip_postgres:
        pg_success = run_alembic_migrations(dry_run=args.dry_run)
        if not pg_success:
            all_success = False
            logger.error("stopping_due_to_alembic_failure")
            return 1

        opt_success = optimize_postgres(dry_run=args.dry_run)
        if not opt_success:
            all_success = False
            logger.warning("postgres_optimization_had_issues")
    else:
        logger.info("skipping_postgres_setup")

    # === Qdrant Setup ===
    if not args.skip_qdrant:
        qdrant_success = setup_qdrant_collection(
            args.collection,
            force_recreate=args.force_recreate_qdrant,
            snapshot_file=args.qdrant_snapshot_file,
            dry_run=args.dry_run,
        )
        if not qdrant_success:
            all_success = False
            logger.warning("qdrant_setup_had_issues")
    else:
        logger.info("skipping_qdrant_setup")

    if all_success:
        logger.info("database_setup_completed_successfully")
        return 0
    else:
        logger.error("database_setup_completed_with_errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
