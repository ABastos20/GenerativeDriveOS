"""Smart re-ingestion with file watching.

Monitors file changes and automatically re-ingests modified/new files
while removing deleted files from Qdrant.
"""

from __future__ import annotations

from pathlib import Path
from typing import Set, Optional
from datetime import datetime
import time

import structlog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from jarvis.database import qdrant as qdrant_db
from jarvis.memory.ingest import ingest_file

logger = structlog.get_logger(__name__)


class JarvisFileEventHandler(FileSystemEventHandler):
    """Handler for file system events - triggers re-ingestion."""

    def __init__(
        self,
        collection_name: str = "jarvis-core",
        debounce_seconds: float = 2.0,
    ):
        self.collection_name = collection_name
        self.debounce_seconds = debounce_seconds
        self.pending_files: Set[str] = set()
        self.last_event_time: float = 0

    def _handle_file_event(self, file_path: str, event_type: str) -> None:
        """Common handler for file events (created/modified)."""
        if not self._is_supported_file(file_path):
            return
        
        logger.info(event_type, path=file_path)
        self.pending_files.add(file_path)
        self.last_event_time = time.time()

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification."""
        if event.is_directory:
            return
        self._handle_file_event(event.src_path, "file_modified")

    def on_created(self, event: FileSystemEvent):
        """Handle file creation."""
        if event.is_directory:
            return
        self._handle_file_event(event.src_path, "file_created")

    def _handle_deletion(self, file_path: str) -> None:
        """Handle file deletion logic."""
        if not self._is_supported_file(file_path):
            return
        logger.info("file_deleted", path=file_path)
        self._remove_from_qdrant(file_path)

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion."""
        if event.is_directory:
            return
        self._handle_deletion(event.src_path)

    def _handle_move(self, event: FileSystemEvent) -> None:
        """Handle file move/rename logic."""
        # Treat as delete + create
        if hasattr(event, 'src_path'):
            self._remove_from_qdrant(event.src_path)

        if hasattr(event, 'dest_path'):
            dest_path = event.dest_path
            if self._is_supported_file(dest_path):
                logger.info("file_moved", old_path=event.src_path, new_path=dest_path)
                self.pending_files.add(dest_path)
                self.last_event_time = time.time()

    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename."""
        if not event.is_directory:
            self._handle_move(event)

    def _process_files_batch(self, files_to_process: list) -> None:
        """Process a batch of pending files."""
        logger.info("processing_pending_files", count=len(files_to_process))

        for file_path in files_to_process:
            try:
                self._reingest_file(file_path)
            except Exception as e:
                logger.error("reingest_error", path=file_path, error=str(e))

    def process_pending_files(self):
        """Process pending file changes (debounced)."""
        if not self.pending_files:
            return

        # Debounce: Wait until no events for N seconds
        if time.time() - self.last_event_time < self.debounce_seconds:
            return

        files_to_process = list(self.pending_files)
        self.pending_files.clear()
        self._process_files_batch(files_to_process)

    def _is_supported_file(self, file_path: str) -> bool:
        """Check if file type is supported for ingestion."""
        from jarvis.memory.file_event_helpers import is_supported_file
        return is_supported_file(file_path)

    def _reingest_file(self, file_path: str):
        """Re-ingest a modified file."""
        from jarvis.memory.file_event_helpers import reingest_file
        reingest_file(file_path, self.collection_name)

    def _remove_from_qdrant(self, file_path: str):
        """Remove chunks associated with a file from Qdrant."""
        from jarvis.memory.file_event_helpers import remove_from_qdrant
        remove_from_qdrant(file_path, self.collection_name)


class FileWatcher:
    """File system watcher for automatic re-ingestion."""

    def __init__(
        self,
        watch_paths: list[str],
        collection_name: str = "jarvis-core",
        debounce_seconds: float = 2.0,
    ):
        self.watch_paths = [Path(p).resolve() for p in watch_paths]
        self.collection_name = collection_name
        self.debounce_seconds = debounce_seconds
        self.observer: Optional[Observer] = None
        self.event_handler = JarvisFileEventHandler(
            collection_name=collection_name,
            debounce_seconds=debounce_seconds,
        )

    def start(self):
        """Start watching file system."""
        self.observer = Observer()

        for watch_path in self.watch_paths:
            if not watch_path.exists():
                logger.warning("watch_path_not_found", path=str(watch_path))
                continue

            self.observer.schedule(
                self.event_handler,
                str(watch_path),
                recursive=True,
            )

            logger.info("watching_path", path=str(watch_path))

        self.observer.start()
        logger.info("file_watcher_started", paths=len(self.watch_paths))

    def stop(self):
        """Stop watching file system."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("file_watcher_stopped")

    def run(self):
        """Run file watcher in foreground (blocking)."""
        self.start()

        try:
            while True:
                # Process pending files periodically
                self.event_handler.process_pending_files()
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("file_watcher_interrupted")
        finally:
            self.stop()


def start_file_watcher(
    watch_paths: list[str],
    collection_name: str = "jarvis-core",
    daemon: bool = False,
):
    """Start file watcher.

    Args:
        watch_paths: List of paths to watch
        collection_name: Qdrant collection name
        daemon: If True, run in background; if False, run in foreground
    """
    watcher = FileWatcher(
        watch_paths=watch_paths,
        collection_name=collection_name,
    )

    if daemon:
        # Run in background thread
        import threading

        thread = threading.Thread(target=watcher.run, daemon=True)
        thread.start()

        logger.info("file_watcher_daemon_started")
        return watcher
    else:
        # Run in foreground (blocking)
        watcher.run()
        return None
