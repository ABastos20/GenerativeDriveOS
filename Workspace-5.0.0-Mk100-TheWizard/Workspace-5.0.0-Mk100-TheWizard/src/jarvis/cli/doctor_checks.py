from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List
from urllib import request, error as urlerror

from jarvis.database import qdrant

Runner = Callable[[List[str]], subprocess.CompletedProcess]


def _default_runner(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str


def check_docker_service(
    service: str,
    compose_file: str = "docker/docker-compose.yml",
    runner: Runner = _default_runner,
) -> CheckResult:
    cmd = ["docker", "compose", "-f", compose_file, "ps", service]
    try:
        result = runner(cmd)
    except FileNotFoundError:
        return CheckResult(service, False, "docker command not found")

    if result.returncode != 0:
        return CheckResult(service, False, result.stderr.strip() or "service not running")

    status = result.stdout.strip()
    if "Up" in status or "running" in status.lower():
        return CheckResult(service, True, "service running")
    return CheckResult(service, False, status or "status unknown")


def check_postgres(
    runner: Runner = _default_runner,
    compose_file: str = "docker/docker-compose.yml",
    user: str = "jarvis",
) -> CheckResult:
    cmd = [
        "docker",
        "compose",
        "-f",
        compose_file,
        "exec",
        "-T",
        "postgres",
        "pg_isready",
        "-U",
        user,
    ]
    try:
        result = runner(cmd)
    except FileNotFoundError:
        return CheckResult("postgres", False, "docker command not found")

    if result.returncode == 0:
        return CheckResult("postgres", True, "pg_isready OK")
    return CheckResult("postgres", False, result.stderr.strip() or result.stdout.strip())


def check_qdrant(url: str = "http://localhost:6333/readyz") -> CheckResult:
    try:
        with request.urlopen(url, timeout=3) as resp:
            if 200 <= resp.status < 300:
                return CheckResult("qdrant", True, "ready")
            return CheckResult("qdrant", False, f"status {resp.status}")
    except urlerror.URLError as exc:
        return CheckResult("qdrant", False, str(exc))


def check_qdrant_collection(
    collection_name: str = "knowledge",
) -> CheckResult:
    """Check if Qdrant collection exists and has correct configuration.

    Validates:
    - Collection exists
    - Vector dimensions (384)
    - Distance metric (Cosine)
    - HNSW parameters (m=16, ef_construct=200)

    Args:
        collection_name: Name of collection to check (default: "knowledge")

    Returns:
        CheckResult with validation status
    """
    try:
        # Get client and check if collection exists
        try:
            client = qdrant.get_qdrant_client()
        except Exception as e:
            return CheckResult(
                f"qdrant-collection-{collection_name}",
                False,
                f"connection failed: {e}",
            )

        if not qdrant.collection_exists(collection_name, client=client):
            return CheckResult(
                f"qdrant-collection-{collection_name}",
                False,
                "collection does not exist (run init to create)",
            )

        # Validate collection configuration
        try:
            info = qdrant.get_collection_info(collection_name, client=client)

            # Check vector dimensions
            if info.config.params.vectors.size != qdrant.VECTOR_SIZE:
                return CheckResult(
                    f"qdrant-collection-{collection_name}",
                    False,
                    (
                        f"wrong vector size: {info.config.params.vectors.size} "
                        f"(expected {qdrant.VECTOR_SIZE})"
                    ),
                )

            # Check distance metric
            if info.config.params.vectors.distance != qdrant.DISTANCE_METRIC:
                return CheckResult(
                    f"qdrant-collection-{collection_name}",
                    False,
                    (
                        f"wrong distance metric: {info.config.params.vectors.distance} "
                        f"(expected {qdrant.DISTANCE_METRIC.value})"
                    ),
                )

            # Check HNSW parameters
            hnsw_config = info.config.hnsw_config
            if hnsw_config.m != qdrant.HNSW_M:
                return CheckResult(
                    f"qdrant-collection-{collection_name}",
                    False,
                    f"wrong HNSW m: {hnsw_config.m} (expected {qdrant.HNSW_M})",
                )

            if hnsw_config.ef_construct != qdrant.HNSW_EF_CONSTRUCT:
                return CheckResult(
                    f"qdrant-collection-{collection_name}",
                    False,
                    f"wrong HNSW ef_construct: {hnsw_config.ef_construct} (expected {qdrant.HNSW_EF_CONSTRUCT})",
                )

            if hnsw_config.full_scan_threshold != qdrant.HNSW_FULL_SCAN_THRESHOLD:
                return CheckResult(
                    f"qdrant-collection-{collection_name}",
                    False,
                    (
                        "wrong HNSW full_scan_threshold: "
                        f"{hnsw_config.full_scan_threshold} "
                        f"(expected {qdrant.HNSW_FULL_SCAN_THRESHOLD})"
                    ),
                )

            # All checks passed
            points_count = info.points_count if hasattr(info, "points_count") else 0
            return CheckResult(
                f"qdrant-collection-{collection_name}",
                True,
                f"configured correctly ({points_count} points)",
            )

        except Exception as e:
            return CheckResult(
                f"qdrant-collection-{collection_name}",
                False,
                f"validation failed: {e}",
            )

    except ImportError as e:
        return CheckResult(
            f"qdrant-collection-{collection_name}",
            False,
            f"qdrant module not available: {e}",
        )


def check_workspace(root: Path = Path("/workspace")) -> CheckResult:
    if not root.exists():
        return CheckResult("workspace", False, f"{root} not found")
    private = root / ".jarvis"
    try:
        private.mkdir(parents=True, exist_ok=True)
        test_file = private / ".doctor"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return CheckResult("workspace", True, f"mounted at {root}")
    except OSError as exc:  # pragma: no cover - depends on host fs
        return CheckResult("workspace", False, str(exc))


def run_all_checks() -> List[CheckResult]:
    results: List[CheckResult] = []
    results.append(check_docker_service("jarvis-app"))
    results.append(check_docker_service("postgres"))
    results.append(check_docker_service("qdrant"))
    results.append(check_postgres())
    results.append(check_qdrant())
    results.append(check_qdrant_collection())  # Validate collection configuration
    results.append(check_workspace())
    return results


def summarize(results: Iterable[CheckResult]) -> dict:
    data = []
    passed = True
    for result in results:
        data.append(
            {"name": result.name, "passed": result.passed, "message": result.message}
        )
        passed &= result.passed
    return {"passed": passed, "checks": data}
