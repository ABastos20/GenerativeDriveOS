"""Database snapshot management for JARVIS.

Provides PostgreSQL database backup and restore capabilities using pg_dump/pg_restore.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Snapshot:
    """Database snapshot metadata."""
    
    name: str
    timestamp: datetime
    path: Path
    size_bytes: int


class SnapshotManager:
    """Manage PostgreSQL database snapshots.
    
    Creates snapshots using pg_dump inside the PostgreSQL container,
    and restores using pg_restore with database recreation.
    """
    
    def __init__(self, snapshot_dir: Path | None = None):
        """Initialize snapshot manager.
        
        Args:
            snapshot_dir: Directory for snapshot storage (default: .jarvis/snapshots)
        """
        if snapshot_dir is None:
            snapshot_dir = Path.home() / ".jarvis" / "snapshots"
        self.snapshot_dir = snapshot_dir
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    def create_snapshot(self, name: str) -> Snapshot:
        """Create database snapshot using pg_dump.
        
        Args:
            name: Snapshot name
            
        Returns:
            Snapshot metadata
            
        Raises:
            subprocess.CalledProcessError: If pg_dump fails
        """
        timestamp = datetime.now()
        filename = f"{name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.sql"
        path = self.snapshot_dir / filename
        
        logger.info("snapshot_create_start", name=name, path=str(path))
        
        # Run pg_dump inside container
        cmd = [
            "docker", "exec", "jarvis-postgres",
            "pg_dump", "-U", "jarvis", "jarvis", "-f", f"/tmp/{filename}"
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Copy from container to host
        cmd_copy = [
            "docker", "cp",
            f"jarvis-postgres:/tmp/{filename}",
            str(path)
        ]
        subprocess.run(cmd_copy, check=True, capture_output=True)
        
        snapshot = Snapshot(
            name=name,
            timestamp=timestamp,
            path=path,
            size_bytes=path.stat().st_size
        )
        logger.info(
            "snapshot_create_complete",
            snapshot=snapshot.name,
            size_mb=f"{snapshot.size_bytes / 1024 / 1024:.2f}"
        )
        return snapshot
    
    def restore_snapshot(self, name: str) -> None:
        """Restore database from snapshot.
        
        WARNING: This will DROP and recreate the database!
        All data since the snapshot will be lost.
        
        Args:
            name: Snapshot name to restore
            
        Raises:
            ValueError: If snapshot not found
            subprocess.CalledProcessError: If restore fails
        """
        snapshots = self.list_snapshots()
        matching = [s for s in snapshots if s.name == name]
        if not matching:
            raise ValueError(f"Snapshot '{name}' not found")
        
        snapshot = matching[-1]  # Most recent with this name
        logger.warning("snapshot_restore_start", snapshot=snapshot.name)
        
        # Copy snapshot to container
        cmd_copy = [
            "docker", "cp",
            str(snapshot.path),
            f"jarvis-postgres:/tmp/{snapshot.path.name}"
        ]
        subprocess.run(cmd_copy, check=True, capture_output=True)
        
        # Drop and recreate database (destructive!)
        cmd_drop = [
            "docker", "exec", "jarvis-postgres",
            "psql", "-U", "jarvis", "-c", "DROP DATABASE IF EXISTS jarvis;"
        ]
        subprocess.run(cmd_drop, check=True, capture_output=True, text=True)
        
        cmd_create = [
            "docker", "exec", "jarvis-postgres",
            "psql", "-U", "jarvis", "-c", "CREATE DATABASE jarvis;"
        ]
        subprocess.run(cmd_create, check=True, capture_output=True, text=True)
        
        # Restore from snapshot
        cmd_restore = [
            "docker", "exec", "jarvis-postgres",
            "psql", "-U", "jarvis", "-d", "jarvis", "-f", f"/tmp/{snapshot.path.name}"
        ]
        subprocess.run(cmd_restore, check=True, capture_output=True, text=True)
        
        logger.info("snapshot_restore_complete", snapshot=snapshot.name)
    
    def list_snapshots(self) -> List[Snapshot]:
        """List all available snapshots.
        
        Returns:
            List of snapshots sorted by timestamp
        """
        snapshots = []
        for path in self.snapshot_dir.glob("*.sql"):
            # Parse name from filename: name_YYYYMMDD_HHMMSS.sql
            parts = path.stem.split("_")
            if len(parts) >= 3:
                name = "_".join(parts[:-2])
                date_str = parts[-2]
                time_str = parts[-1]
                try:
                    timestamp = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    snapshots.append(Snapshot(
                        name=name,
                        timestamp=timestamp,
                        path=path,
                        size_bytes=path.stat().st_size
                    ))
                except ValueError:
                    # Skip files with invalid timestamp format
                    logger.warning("snapshot_parse_error", file=path.name)
                    continue
        return sorted(snapshots, key=lambda s: s.timestamp)
    
    def delete_snapshot(self, name: str) -> None:
        """Delete snapshot(s) by name.
        
        Args:
            name: Snapshot name to delete
            
        Raises:
            ValueError: If snapshot not found
        """
        snapshots = [s for s in self.list_snapshots() if s.name == name]
        if not snapshots:
            raise ValueError(f"Snapshot '{name}' not found")
        
        for snapshot in snapshots:
            snapshot.path.unlink()
            logger.info("snapshot_deleted", snapshot=snapshot.name, timestamp=snapshot.timestamp)
