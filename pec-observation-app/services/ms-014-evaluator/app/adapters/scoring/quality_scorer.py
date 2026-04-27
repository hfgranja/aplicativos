"""Quality scoring for AI-generated feedback against the human-approved version.

Produces a composite quality score (0.0 – 1.0) from five independent dimensions:

  structural_score  — required keys present and non-empty
  evidence_score    — each strength/improvement has a non-empty evidence citation
  delta_score       — 1 − edit_ratio (low edits = high quality)
  guardrail_score   — output respects safety rules (no student names, no slurs)
  semantic_score    — cosine similarity between AI draft text and approved text
                      (requires embeddings, optional — 0.5 default if unavailable)

Final composite:
  quality = structural*0.25 + evidence*0.25 + delta*0.25 + guardrail*0.15 + semantic*0.10
"""
import json
import logging
import math
import re
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

_REQUIRED_KEYS = {"summary", "strengths", "improvement_points",
                  "evidence", "suggested_action_plan"}

_FORBIDDEN_PATTERNS = [
    r"\balun[oa]s?\b",        # student names context
    r"incompetente",
    r"irrespons[aá]vel",
    r"falhou completamente",
    r"n[aã]o sabe ensinar",
    r"p[eé]ssim[oa]",
]


@dataclass
class QualityReport:
    structural_score: float = 0.0
    evidence_score:   float = 0.0
    delta_score:      float = 0.0
    guardrail_score:  float = 0.0
    semantic_score:   float = 0.5
    quality_score:    float = 0.0
    details:          dict  = field(default_factory=dict)


def _structural(ai_feedback: dict) -> tuple[float, dict]:
    """Check required keys and minimal content depth."""
    present = sum(1 for k in _REQUIRED_KEYS if ai_feedback.get(k))
    ratio = present / len(_REQUIRED_KEYS)
    # Bonus: strengths and improvement_points are non-empty lists
    bonus = 0.0
    if isinstance(ai_feedback.get("strengths"), list) and ai_feedback["strengths"]:
        bonus += 0.05
    if isinstance(ai_feedback.get("improvement_points"), list) and ai_feedback["improvement_points"]:
        bonus += 0.05
    return min(1.0, ratio + bonus), {"keys_present": present, "keys_total": len(_REQUIRED_KEYS)}


def _evidence(ai_feedback: dict) -> tuple[float, dict]:
    """Every strength/improvement should have a non-empty evidence field."""
    items = (
        list(ai_feedback.get("strengths", []))
        + list(ai_feedback.get("improvement_points", []))
    )
    if not items:
        return 0.0, {"items_checked": 0}
    with_evidence = sum(
        1 for item in items
        if isinstance(item, dict) and item.get("evidence", "").strip()
    )
    ratio = with_evidence / len(items)
    return ratio, {"items_with_evidence": with_evidence, "items_total": len(items)}


def _delta(ai_text: str, human_text: str) -> tuple[float, dict]:
    """Token-level Jaccard similarity as proxy for edit ratio.

    High Jaccard = few changes = high delta_score.
    """
    a_tokens = set(ai_text.lower().split())
    h_tokens = set(human_text.lower().split())
    if not a_tokens and not h_tokens:
        return 1.0, {"jaccard": 1.0}
    if not a_tokens or not h_tokens:
        return 0.0, {"jaccard": 0.0}
    inter = len(a_tokens & h_tokens)
    union = len(a_tokens | h_tokens)
    jaccard = inter / union
    return jaccard, {"jaccard": round(jaccard, 4)}


def _guardrail(ai_text: str) -> tuple[float, dict]:
    """Check no forbidden patterns appear in the AI output."""
    violations = []
    for pattern in _FORBIDDEN_PATTERNS:
        if re.search(pattern, ai_text, re.IGNORECASE):
            violations.append(pattern)
    score = 1.0 if not violations else max(0.0, 1.0 - 0.25 * len(violations))
    return score, {"violations": violations}


def _cosine(vec_a: list[float], vec_b: list[float]) -> float:
    if len(vec_a) != len(vec_b):
        return 0.5
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(x * x for x in vec_a))
    mag_b = math.sqrt(sum(x * x for x in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.5
    return max(0.0, min(1.0, dot / (mag_a * mag_b)))


def _semantic(
    ai_text: str, human_text: str,
    ollama_base_url: str, embedding_model: str,
) -> tuple[float, dict]:
    try:
        def _embed(t):
            r = httpx.post(
                f"{ollama_base_url}/api/embeddings",
                json={"model": embedding_model, "prompt": t[:4000]},
                timeout=30.0,
            )
            r.raise_for_status()
            return r.json()["embedding"]

        vec_ai    = _embed(ai_text)
        vec_human = _embed(human_text)
        sim = _cosine(vec_ai, vec_human)
        return sim, {"cosine_similarity": round(sim, 4)}
    except Exception as exc:
        logger.warning("Semantic scoring failed (using 0.5 default): %s", exc)
        return 0.5, {"error": str(exc)}


def score(
    ai_feedback: dict,
    human_feedback: dict,
    ollama_base_url: str,
    embedding_model: str,
    compute_semantic: bool = True,
) -> QualityReport:
    ai_text    = json.dumps(ai_feedback,    ensure_ascii=False)
    human_text = json.dumps(human_feedback, ensure_ascii=False)

    struct_s,  struct_d   = _structural(ai_feedback)
    evid_s,    evid_d     = _evidence(ai_feedback)
    delta_s,   delta_d    = _delta(ai_text, human_text)
    guard_s,   guard_d    = _guardrail(ai_text)

    if compute_semantic:
        sem_s, sem_d = _semantic(ai_text, human_text, ollama_base_url, embedding_model)
    else:
        sem_s, sem_d = 0.5, {"skipped": True}

    quality = (
        struct_s * 0.25
        + evid_s  * 0.25
        + delta_s * 0.25
        + guard_s * 0.15
        + sem_s   * 0.10
    )

    return QualityReport(
        structural_score = round(struct_s, 4),
        evidence_score   = round(evid_s,   4),
        delta_score      = round(delta_s,  4),
        guardrail_score  = round(guard_s,  4),
        semantic_score   = round(sem_s,    4),
        quality_score    = round(quality,  4),
        details={
            "structural": struct_d,
            "evidence":   evid_d,
            "delta":      delta_d,
            "guardrail":  guard_d,
            "semantic":   sem_d,
        },
    )
