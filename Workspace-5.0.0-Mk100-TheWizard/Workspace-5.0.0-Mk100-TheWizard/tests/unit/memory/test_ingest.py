from __future__ import annotations

from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from jarvis.memory import ingest


def test_detect_format_markdown() -> None:
    assert ingest.detect_format(Path("doc.md")) == "markdown"
    assert ingest.detect_format(Path("doc.markdown")) == "markdown"
    assert ingest.detect_format(Path("doc.txt")) == "markdown"


def test_detect_format_pdf_html() -> None:
    assert ingest.detect_format(Path("doc.pdf")) == "pdf"
    assert ingest.detect_format(Path("doc.html")) == "html"


def test_detect_format_unsupported() -> None:
    with pytest.raises(ValueError):
        ingest.detect_format(Path("image.png"))


def test_convert_to_markdown_passthrough(tmp_path: Path) -> None:
    md_file = tmp_path / "sample.md"
    md_file.write_text("# Title\n\nContent", encoding="utf-8")

    converted = ingest.convert_to_markdown(md_file, "markdown")

    assert "Title" in converted
    assert "Content" in converted


def test_chunk_text_basic() -> None:
    text = "Para one.\n\nPara two which is a bit longer.\n\nPara three."
    chunks = ingest.chunk_text(text, max_chars=30, overlap=5)
    assert len(chunks) >= 2
    assert all(chunks)


def test_ingest_file_with_mocks(tmp_path: Path) -> None:
    document = tmp_path / "sample.md"
    document.write_text("# Title\n\nBody paragraph here.", encoding="utf-8")

    stub_vectors: List[List[float]] = [[0.1] * ingest.qdrant.VECTOR_SIZE] * 2

    mock_client = MagicMock()

    with patch.object(ingest.qdrant, "get_qdrant_client", return_value=mock_client), patch.object(
        ingest.qdrant, "init_collection"
    ) as mock_init:
        result = ingest.ingest_file(
            document,
            collection_name="test_collection",
            embed_fn=lambda texts: stub_vectors[: len(texts)],
            client=None,
        )

    mock_init.assert_called_once()
    mock_client.upsert.assert_called_once()
    assert result.collection_name == "test_collection"
    assert result.points_written == result.chunks
    assert result.vector_size == ingest.qdrant.VECTOR_SIZE
