"""Unit tests for RAG query use case (mocked embedding + DB)."""
from unittest.mock import MagicMock, patch

from app.application.use_cases.rag_query import retrieve_context


def test_retrieve_context_empty_when_embed_fails():
    db = MagicMock()
    with patch(
        "app.application.use_cases.rag_query.embed",
        side_effect=RuntimeError("ollama down"),
    ):
        result = retrieve_context(db, "aula de matemática")
    assert result == []


def test_retrieve_context_returns_chunks():
    db = MagicMock()
    mock_record = MagicMock()
    mock_record.source_type = "knowledge_document"
    mock_record.source_id = "doc-1"
    mock_record.content = "Currículo Paulista..."
    mock_record.metadata_ = {"title": "CP 2024"}

    with (
        patch("app.application.use_cases.rag_query.embed", return_value=[0.1] * 768),
        patch(
            "app.application.use_cases.rag_query.similarity_search",
            return_value=[mock_record],
        ),
    ):
        result = retrieve_context(db, "planejamento curricular")

    assert len(result) == 1
    assert result[0]["source_id"] == "doc-1"
    assert result[0]["content"] == "Currículo Paulista..."
