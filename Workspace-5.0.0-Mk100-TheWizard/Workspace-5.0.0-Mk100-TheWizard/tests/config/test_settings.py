from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.config import load_settings


class SettingsLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.tempdir.name) / "settings.yaml"
        self.dotenv_path = Path(self.tempdir.name) / ".env"
        config = {
            "project": {"name": "Test Project", "environment": "development"},
            "workspace": {"root": "/tmp/workspace", "private_dir": ".jarvis"},
            "providers": [
                {
                    "name": "openrouter",
                    "type": "free_tier",
                    "priority": 1,
                    "model": "openrouter/test",
                    "api_key_env": "OPENROUTER_API_KEY",
                }
            ],
        }
        self.config_path.write_text(json.dumps(config), encoding="utf-8")
        self.dotenv_path.write_text("OPENROUTER_API_KEY=test-secret\n", encoding="utf-8")

    def tearDown(self) -> None:
        os.environ.pop("OPENROUTER_API_KEY", None)
        os.environ.pop("WORKSPACE_ROOT", None)
        os.environ.pop("WORKSPACE_PRIVATE_DIR", None)
        self.tempdir.cleanup()

    def test_load_settings_reads_config_and_env(self) -> None:
        settings = load_settings(self.config_path, self.dotenv_path)
        self.assertEqual(settings.project_name, "Test Project")
        self.assertEqual(settings.workspace.root, Path("/tmp/workspace"))
        provider = settings.providers[0]
        self.assertEqual(provider.api_key(), "test-secret")

    def test_env_overrides_workspace(self) -> None:
        os.environ["WORKSPACE_ROOT"] = "/override"
        os.environ["WORKSPACE_PRIVATE_DIR"] = ".custom"
        settings = load_settings(self.config_path, self.dotenv_path)
        self.assertEqual(settings.workspace.root, Path("/override"))
        self.assertEqual(settings.workspace.private_dir, ".custom")


if __name__ == "__main__":
    unittest.main()
