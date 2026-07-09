from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable, Iterator, Optional

LOGGER = logging.getLogger(__name__)


def _load_patterns(root: Path, filenames: Iterable[str]) -> list[str]:
    patterns: list[str] = []
    for fname in filenames:
        file_path = root / fname
        if not file_path.exists():
            continue
        for line in file_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)
    return patterns


def _matches(patterns: list[str], rel_path: Path) -> bool:
    posix = rel_path.as_posix()
    for pattern in patterns:
        if pattern.endswith("/"):
            if posix.startswith(pattern.rstrip("/")):
                return True
            continue
        if fnmatch(posix, pattern):
            return True
    return False


@dataclass
class Workspace:
    """Abstraction around the mounted workspace directory."""

    root: Path = Path("/workspace")
    private_dir_name: str = ".jarvis"
    ignore_files: tuple[str, ...] = (".gitignore", ".jarvisignore")

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        self._private_dir = (self.root / self.private_dir_name).resolve()
        self._patterns = _load_patterns(self.root, self.ignore_files)
        self._ignore_names = {Path(name).name for name in self.ignore_files}

    def ensure_private_dir(self) -> Path:
        self._private_dir.mkdir(parents=True, exist_ok=True)
        return self._private_dir

    def _normalize(self, path: Path | str) -> Path:
        candidate = (self.root / Path(path)).resolve()
        if not str(candidate).startswith(str(self.root)):
            raise ValueError(f"Path {candidate} escapes workspace root {self.root}")
        return candidate

    def is_ignored(self, path: Path | str) -> bool:
        rel = self.relative_path(path)
        if rel is None:
            return True
        if rel.parts and rel.parts[0] == self.private_dir_name.lstrip("./"):
            return True
        if rel.name in self._ignore_names:
            return True
        return _matches(self._patterns, rel)

    def relative_path(self, path: Path | str) -> Optional[Path]:
        candidate = self._normalize(path)
        try:
            return candidate.relative_to(self.root)
        except ValueError:
            return None

    def iter_ingestable_files(
        self, extensions: Optional[Iterable[str]] = None
    ) -> Iterator[Path]:
        exts = {ext.lower() for ext in extensions} if extensions else None
        for path in self.root.rglob("*"):
            if path.is_dir():
                continue
            if self.is_ignored(path):
                LOGGER.debug("Skipping ignored file", extra={"file": str(path)})
                continue
            if exts and path.suffix.lower() not in exts:
                continue
            yield path

    def open_file(self, relative_path: Path | str, mode: str = "r"):
        target = self._normalize(relative_path)
        return open(target, mode, encoding="utf-8")

    def write_private(self, relative_path: Path | str, data: str) -> Path:
        self.ensure_private_dir()
        target = (self._private_dir / Path(relative_path)).resolve()
        if not str(target).startswith(str(self._private_dir)):
            raise ValueError("Private writes must stay within .jarvis directory")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")
        return target

    def describe(self) -> dict[str, str]:
        stat = self.ensure_private_dir().stat()
        return {
            "root": str(self.root),
            "private_dir": str(self._private_dir),
            "private_owner": f"{stat.st_uid}:{stat.st_gid}",
            "ignore_source": ", ".join(self.ignore_files),
            "patterns": ", ".join(self._patterns) or "none",
        }


def detect_host_ids() -> tuple[int, int]:
    uid = int(os.environ.get("HOST_UID", os.getuid()))
    gid = int(os.environ.get("HOST_GID", os.getgid()))
    return uid, gid
