import time
from pathlib import Path

from jarvis.indices.code_index import CodeIndex


def test_code_index_builds_and_searches(tmp_path):
    file_path = tmp_path / "module.py"
    file_path.write_text(
        "import os\n\n"
        "def foo():\n"
        "    return 1\n\n"
        "class Bar:\n"
        "    def baz(self):\n"
        "        return 'ok'\n"
    )

    index = CodeIndex(root=tmp_path, enable_embeddings=True, max_snippet_lines=5)
    results = index.search("foo", limit=5)
    assert results, "Expected search results for foo"
    assert results[0].name == "foo"
    assert results[0].kind == "function"
    assert results[0].embedding is not None
    assert "foo(" in index.to_prompt_context("foo")


def test_refresh_updates_index(tmp_path):
    file_path = tmp_path / "module.py"
    file_path.write_text("def alpha():\n    return 1\n")
    index = CodeIndex(root=tmp_path)
    assert any(item.name == "alpha" for item in index.snapshot())

    file_path.write_text("def beta():\n    return 2\n")
    index.refresh()

    names = [item.name for item in index.snapshot()]
    assert "beta" in names
    assert "alpha" not in names


def test_refresh_removes_deleted_files(tmp_path):
    path1 = tmp_path / "a.py"
    path1.write_text("def a():\n    return 1\n")
    index = CodeIndex(root=tmp_path)
    assert any(item.path.endswith("a.py") for item in index.snapshot())

    path1.unlink()
    index.refresh()

    assert not any(item.path.endswith("a.py") for item in index.snapshot())
