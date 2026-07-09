"""Lightweight code index for grounding Jarvis prompts (Story 11-4).

Builds a searchable index of functions, classes, and modules with optional
embeddings and incremental refresh support.
"""

from __future__ import annotations

import ast
import hashlib
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CodeItem:
    """Indexed code artifact."""

    file_path: str
    path: str
    name: str
    kind: str  # class | function | module
    signature: Optional[str]
    snippet: str
    dependencies: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None


class CodeIndex:
    """File-system backed code index with incremental refresh."""

    def __init__(
        self,
        root: Path | str = Path("src"),
        enable_embeddings: bool = False,
        max_snippet_lines: int = 32,
    ) -> None:
        self.root = Path(root)
        self.enable_embeddings = enable_embeddings
        self.max_snippet_lines = max_snippet_lines
        self._index: Dict[str, List[CodeItem]] = {}
        self._mtimes: Dict[Path, float] = {}
        self._digests: Dict[Path, str] = {}
        self._lock = threading.Lock()

        if not self.root.exists():
            logger.warning("code_index_root_missing", root=str(self.root))
            return

        self.build_index()

    # ---- Public API -----------------------------------------------------

    def build_index(self) -> None:
        """Build the index from scratch."""
        with self._lock:
            self._index.clear()
            self._mtimes.clear()
            self._digests.clear()
            for path in self._python_files():
                self._index_file(path)

    def refresh(self) -> None:
        """Incrementally refresh the index based on file mtimes."""
        if not self.root.exists():
            return

        with self._lock:
            current_files = set(self._python_files())
            known_files = set(self._mtimes.keys())

            # Handle deletions
            for removed in known_files - current_files:
                self._index.pop(str(removed), None)
                self._mtimes.pop(removed, None)
                self._digests.pop(removed, None)

            # Handle new or modified files (skip unchanged for large trees)
            for path in current_files:
                mtime = path.stat().st_mtime_ns
                prev_mtime = self._mtimes.get(path)
                if prev_mtime is None or mtime > prev_mtime:
                    self._index_file(path)
                else:
                    # If mtime precision is coarse, compare digest to detect in-place edits.
                    prev_digest = self._digests.get(path)
                    current_digest = self._hash_text(path.read_text(encoding="utf-8"))
                    if current_digest != prev_digest:
                        self._index_file(path)

    def search(self, query: str, limit: int = 10) -> List[CodeItem]:
        """Search the index by name/snippet/dependencies."""
        if not self._index:
            self.build_index()

        tokens = [t for t in query.lower().split() if t]
        if not tokens:
            return []

        results: List[Tuple[float, CodeItem]] = []
        for items in self._index.values():
            for item in items:
                haystack = " ".join(
                    [item.name.lower(), item.snippet.lower(), " ".join(item.dependencies)]
                )
                score = sum(self._token_score(token, item, haystack) for token in tokens)
                if score > 0:
                    results.append((score, item))

        results.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in results[:limit]]

    def to_prompt_context(self, query: str, limit: int = 5) -> str:
        """Return a BMAD-friendly grounding snippet for LLM prompts."""
        matches = self.search(query, limit=limit)
        lines = []
        for item in matches:
            lines.append(f"{item.kind.upper()}: {item.name} ({item.path})")
            if item.signature:
                lines.append(f"  signature: {item.signature}")
            if item.dependencies:
                lines.append(f"  deps: {', '.join(sorted(set(item.dependencies)))}")
            lines.append("  snippet:")
            for snippet_line in item.snippet.splitlines():
                lines.append(f"    {snippet_line}")
            lines.append("")  # spacer
        return "\n".join(lines)

    def snapshot(self) -> List[CodeItem]:
        """Return a flattened view of all indexed items."""
        items: List[CodeItem] = []
        for entry in self._index.values():
            items.extend(entry)
        return items

    # ---- Internal helpers -----------------------------------------------

    def _python_files(self) -> Iterable[Path]:
        return (
            path
            for path in self.root.rglob("*.py")
            if "__pycache__" not in path.parts and ".venv" not in path.parts
        )

    def _index_file(self, path: Path) -> None:
        try:
            source = path.read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("code_index_read_failed", path=str(path), error=str(exc))
            return

        try:
            tree = ast.parse(source, type_comments=True)
        except SyntaxError as exc:  # pragma: no cover - defensive
            logger.warning("code_index_parse_failed", path=str(path), error=str(exc))
            return

        dependencies = self._extract_dependencies(tree)
        items: List[CodeItem] = []

        # Always index the module for docstrings and file-level grounding.
        module_snippet = self._build_snippet(source, 1, min(self.max_snippet_lines, len(source.splitlines())))
        items.append(
            CodeItem(
                file_path=path.name,
                path=str(path),
                name=path.name,
                kind="module",
                signature=None,
                snippet=module_snippet,
                dependencies=list(dependencies),
                embedding=self._compute_embedding(source) if self.enable_embeddings else None,
            )
        )

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                items.append(
                    CodeItem(
                        file_path=path.name,
                        path=str(path),
                        name=node.name,
                        kind="function",
                        signature=self._get_signature(node),
                        snippet=self._build_snippet(source, node.lineno, getattr(node, "end_lineno", None)),
                        dependencies=list(dependencies),
                        embedding=self._compute_embedding(source) if self.enable_embeddings else None,
                    )
                )
            elif isinstance(node, ast.ClassDef):
                class_snippet = self._build_snippet(source, node.lineno, getattr(node, "end_lineno", None))
                items.append(
                    CodeItem(
                        file_path=node.name,
                        path=str(path),
                        name=node.name,
                        kind="class",
                        signature=self._get_class_signature(node),
                        snippet=class_snippet,
                        dependencies=list(dependencies),
                        embedding=self._compute_embedding(source) if self.enable_embeddings else None,
                    )
                )
                # Index class methods
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        items.append(
                            CodeItem(
                                file_path=f"{node.name}.{sub.name}",
                                path=str(path),
                                name=f"{node.name}.{sub.name}",
                                kind="method",
                                signature=self._get_signature(sub),
                                snippet=self._build_snippet(source, sub.lineno, getattr(sub, "end_lineno", None)),
                                dependencies=list(dependencies),
                                embedding=self._compute_embedding(source) if self.enable_embeddings else None,
                            )
                        )

        self._index[str(path)] = items
        self._mtimes[path] = path.stat().st_mtime_ns
        self._digests[path] = self._hash_text(source)
        logger.debug("code_indexed_file", path=str(path), item_count=len(items))

    def _build_snippet(self, source: str, start_line: int, end_line: Optional[int]) -> str:
        lines = source.splitlines()
        end_line = end_line or min(len(lines), start_line + self.max_snippet_lines)
        window_end = min(end_line, start_line + self.max_snippet_lines)
        snippet_lines = lines[start_line - 1 : window_end]
        return "\n".join(snippet_lines).strip()

    def _extract_dependencies(self, tree: ast.AST) -> List[str]:
        deps: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                deps.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                deps.append(node.module)
        return deps

    def _get_signature(self, node: ast.AST) -> Optional[str]:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return None
        args = [arg.arg for arg in node.args.args]
        return f"{node.name}({', '.join(args)})"

    def _get_class_signature(self, node: ast.ClassDef) -> str:
        if not node.bases:
            return node.name
        bases = []
        for base in node.bases:
            try:
                bases.append(ast.unparse(base))
            except Exception:
                bases.append(getattr(base, "id", "") or getattr(base, "attr", ""))
        return f"{node.name}({', '.join(filter(None, bases))})"

    def _token_score(self, token: str, item: CodeItem, haystack: str) -> float:
        score = 0.0
        if token in item.name.lower():
            score += 2.0
        if token in haystack:
            score += 1.0
        if token in " ".join(item.dependencies).lower():
            score += 0.5
        return score

    def _hash_text(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _compute_embedding(self, text: str) -> List[float]:
        """Cheap deterministic embedding (hash-based) to avoid extra deps."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Take first 16 bytes and normalize to 0..1
        return [round(byte / 255.0, 4) for byte in digest[:16]]
