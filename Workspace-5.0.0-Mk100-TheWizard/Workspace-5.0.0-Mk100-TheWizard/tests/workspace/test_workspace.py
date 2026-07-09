from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from jarvis.workspace import Workspace


class WorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        (root / ".gitignore").write_text("ignored.txt\nsecrets/\n", encoding="utf-8")
        (root / "kept.txt").write_text("keep me", encoding="utf-8")
        (root / "ignored.txt").write_text("skip", encoding="utf-8")
        (root / "secrets").mkdir()
        # Use a safe, non-sensitive placeholder for tests
        (root / "secrets" / "passwords.txt").write_text("placeholder-password", encoding="utf-8")
        self.workspace = Workspace(root=root)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_iter_ingestable_files_respects_gitignore(self) -> None:
        files = list(self.workspace.iter_ingestable_files())
        self.assertEqual([f.name for f in files], ["kept.txt"])

    def test_write_private_creates_file_in_private_dir(self) -> None:
        target = self.workspace.write_private("logs/output.txt", "hello")
        self.assertTrue(target.exists())
        self.assertTrue(target.is_file())
        rel = target.relative_to(self.workspace.root)
        self.assertTrue(str(rel).startswith(".jarvis"))
        self.assertEqual(target.read_text(encoding="utf-8"), "hello")

    def test_path_escape_is_blocked(self) -> None:
        with self.assertRaises(ValueError):
            self.workspace.open_file("../outside.txt")


if __name__ == "__main__":
    unittest.main()
