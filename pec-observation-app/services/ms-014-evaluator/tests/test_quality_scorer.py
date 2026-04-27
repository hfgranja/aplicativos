"""Unit tests for the quality scorer — no Ollama/DB required."""
from unittest.mock import patch

from app.adapters.scoring.quality_scorer import score, _structural, _evidence, _delta, _guardrail


_GOOD_AI = {
    "summary": "Aula bem conduzida com clareza didática.",
    "strengths": [
        {"title": "Engajamento", "description": "Alunos participaram.", "evidence": "Trecho X"}
    ],
    "improvement_points": [
        {"title": "Tempo", "description": "Gestão pode melhorar.", "evidence": "Trecho Y"}
    ],
    "evidence": [
        {"category": "Didática", "evidence_text": "Trecho Z", "interpretation": "Positivo",
         "confidence": "high"}
    ],
    "suggested_action_plan": [
        {"action": "Planejar temporizador", "owner": "Professor",
         "due_date_suggestion": "2 semanas", "expected_evidence": "Aula cronometrada"}
    ],
    "risks_and_uncertainties": [],
}

_GOOD_HUMAN = dict(_GOOD_AI)  # minimal edit


def test_structural_full_score():
    score_, detail = _structural(_GOOD_AI)
    assert score_ >= 0.9


def test_structural_missing_keys():
    bad = {"summary": "ok"}
    score_, _ = _structural(bad)
    assert score_ < 0.5


def test_evidence_all_present():
    score_, d = _evidence(_GOOD_AI)
    assert score_ == 1.0


def test_evidence_missing():
    bad = {
        "strengths": [{"title": "X", "description": "Y", "evidence": ""}],
        "improvement_points": [],
    }
    score_, _ = _evidence(bad)
    assert score_ == 0.0


def test_delta_identical():
    score_, d = _delta("hello world test", "hello world test")
    assert score_ == 1.0


def test_delta_completely_different():
    score_, d = _delta("abc def ghi", "xyz uvw rst")
    assert score_ == 0.0


def test_guardrail_clean():
    score_, d = _guardrail("Boa aula com bons resultados.")
    assert score_ == 1.0
    assert d["violations"] == []


def test_guardrail_violation():
    score_, d = _guardrail("O professor é incompetente.")
    assert score_ < 1.0
    assert len(d["violations"]) > 0


def test_full_score_with_mocked_semantic():
    with patch(
        "app.adapters.scoring.quality_scorer._semantic",
        return_value=(0.9, {"cosine_similarity": 0.9}),
    ):
        report = score(
            ai_feedback=_GOOD_AI,
            human_feedback=_GOOD_HUMAN,
            ollama_base_url="http://ollama:11434",
            embedding_model="nomic-embed-text",
            compute_semantic=True,
        )
    assert report.quality_score > 0.80
    assert report.guardrail_score == 1.0
