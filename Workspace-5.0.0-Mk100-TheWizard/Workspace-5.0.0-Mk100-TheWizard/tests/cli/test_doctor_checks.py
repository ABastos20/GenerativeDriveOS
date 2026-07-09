from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.cli import doctor_checks
from jarvis.database import qdrant as qdrant_module


class DoctorCheckTests(unittest.TestCase):
    def test_check_docker_service_success(self) -> None:
        def runner(cmd):
            return SimpleNamespace(returncode=0, stdout="Up 2 minutes", stderr="")

        result = doctor_checks.check_docker_service("jarvis", runner=runner)
        self.assertTrue(result.passed)

    def test_check_docker_service_failure(self) -> None:
        def runner(cmd):
            return SimpleNamespace(returncode=1, stdout="", stderr="error")

        result = doctor_checks.check_docker_service("jarvis", runner=runner)
        self.assertFalse(result.passed)
        self.assertEqual(result.message, "error")

    def test_check_qdrant_fail(self) -> None:
        result = doctor_checks.check_qdrant(url="http://localhost:65500/readyz")
        self.assertFalse(result.passed)

    def test_check_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = doctor_checks.check_workspace(root)
            self.assertTrue(result.passed)

    def test_summarize(self) -> None:
        summary = doctor_checks.summarize(
            [
                doctor_checks.CheckResult("a", True, "ok"),
                doctor_checks.CheckResult("b", False, "bad"),
            ]
        )
        self.assertFalse(summary["passed"])
        self.assertEqual(len(summary["checks"]), 2)

    def test_check_qdrant_collection_success(self) -> None:
        vectors = SimpleNamespace(size=qdrant_module.VECTOR_SIZE, distance=qdrant_module.DISTANCE_METRIC)
        hnsw = SimpleNamespace(
            m=qdrant_module.HNSW_M,
            ef_construct=qdrant_module.HNSW_EF_CONSTRUCT,
            full_scan_threshold=qdrant_module.HNSW_FULL_SCAN_THRESHOLD,
        )
        config = SimpleNamespace(params=SimpleNamespace(vectors=vectors), hnsw_config=hnsw)
        info = SimpleNamespace(config=config, points_count=0)

        with patch.object(qdrant_module, "get_qdrant_client") as mock_client, patch.object(
            qdrant_module, "collection_exists", return_value=True
        ) as mock_exists, patch.object(
            qdrant_module, "get_collection_info", return_value=info
        ) as mock_info:
            result = doctor_checks.check_qdrant_collection("knowledge")

        self.assertTrue(result.passed)
        self.assertIn("configured correctly", result.message)
        mock_client.assert_called_once()
        mock_exists.assert_called_once_with("knowledge", client=mock_client.return_value)
        mock_info.assert_called_once_with("knowledge", client=mock_client.return_value)


if __name__ == "__main__":
    unittest.main()
