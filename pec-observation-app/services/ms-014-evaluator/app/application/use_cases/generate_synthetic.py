"""Synthetic training example generator.

When model health degrades, generates diverse paraphrases of high-quality
approved examples using Ollama, then pushes them to MS-013 as additional
training signal — preventing the model from forgetting well-established patterns.

Strategy:
  1. Select top-K highest-quality evaluations from the DB
  2. For each, ask Ollama to produce a *different* transcription scenario
     that would justify a structurally similar feedback
  3. Push each synthetic pair to MS-013 /ingest/feedback with a reduced weight
  4. Store the synthetic example locally for audit
"""
from __future__ import annotations

import json
import logging
import uuid

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.evaluation import FeedbackEvaluation, SyntheticExample

logger = logging.getLogger(__name__)

_GENERATION_PROMPT = """\
Você é um gerador de dados de treinamento para um modelo de avaliação pedagógica.

Dado o feedback pedagógico REFERÊNCIA abaixo, crie UMA nova situação diferente
de observação de aula que justificaria um feedback estruturalmente semelhante.

O feedback deve:
- Ser uma observação DIFERENTE (outro contexto, disciplina ou dinâmica de classe)
- Manter os mesmos padrões de qualidade do feedback original
- Conter pontos fortes, pontos de melhoria e evidências textuais
- Ter entre 150 e 300 palavras de transcrição
- Retornar JSON com exatamente dois campos: "transcription" e "feedback"
  onde "feedback" segue o schema padrão do PEC Pedagogo

FEEDBACK REFERÊNCIA:
{reference_feedback}

Retorne APENAS JSON válido, sem texto extra."""


def generate_for_feedback(db: Session, anchor_feedback_id: str, count: int = 1) -> list[str]:
    """Generate *count* synthetic examples derived from *anchor_feedback_id*.

    Returns list of generated synthetic example IDs.
    """
    # Find the anchor evaluation
    anchor = db.query(FeedbackEvaluation).filter_by(feedback_id=anchor_feedback_id).first()
    if not anchor or anchor.quality_score < settings.min_example_quality:
        logger.debug("Anchor %s has insufficient quality (%.2f) — skipping synthesis",
                     anchor_feedback_id, anchor.quality_score if anchor else 0)
        return []

    generated_ids = []
    for _ in range(min(count, settings.max_synthetic_per_cycle)):
        synthetic_id = _generate_one(db, anchor)
        if synthetic_id:
            generated_ids.append(synthetic_id)

    return generated_ids


def generate_batch_for_health_recovery(db: Session) -> int:
    """Pick top-K examples and generate synthetic variants for each.

    Called when model health status is 'degraded'.
    Returns total synthetic examples created.
    """
    top_anchors = (
        db.query(FeedbackEvaluation)
        .filter(FeedbackEvaluation.quality_score >= settings.min_example_quality)
        .order_by(FeedbackEvaluation.quality_score.desc())
        .limit(3)
        .all()
    )
    total = 0
    for anchor in top_anchors:
        ids = generate_for_feedback(db, anchor.feedback_id, count=2)
        total += len(ids)
    logger.info("Synthetic batch recovery: generated %d examples from %d anchors",
                total, len(top_anchors))
    return total


def _generate_one(db: Session, anchor: FeedbackEvaluation) -> str | None:
    ref_data = anchor.details.get("_human_feedback_snapshot", {})
    if not ref_data:
        logger.debug("No human feedback snapshot for anchor %s", anchor.feedback_id)
        return None

    prompt = _GENERATION_PROMPT.format(
        reference_feedback=json.dumps(ref_data, ensure_ascii=False, indent=2)
    )

    try:
        resp = httpx.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model":  settings.ollama_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        content = json.loads(resp.json()["message"]["content"])
        transcription = content.get("transcription", "")
        feedback      = content.get("feedback", {})
        if not transcription or not feedback:
            return None
    except Exception as exc:
        logger.warning("Synthetic generation via Ollama failed: %s", exc)
        return None

    # Store synthetic example locally
    syn = SyntheticExample(
        source_feedback_id    = anchor.feedback_id,
        transcription_variant = transcription,
        feedback_variant      = json.dumps(feedback, ensure_ascii=False),
        generation_method     = "ollama_paraphrase",
        quality_score         = anchor.quality_score * 0.80,  # synthetic gets discounted score
    )
    db.add(syn)
    db.commit()
    db.refresh(syn)

    # Push to MS-013 Learning Engine with discounted weight
    _push_to_learning(syn)
    logger.info("Created synthetic example %s from anchor %s", syn.id, anchor.feedback_id)
    return str(syn.id)


def _push_to_learning(syn: SyntheticExample) -> None:
    try:
        feedback_dict = json.loads(syn.feedback_variant)
        httpx.post(
            f"{settings.learning_service_url}/api/v1/learning/ingest/feedback",
            json={
                "feedback_id":           f"synthetic:{syn.id}",
                "transcription_snippet": syn.transcription_variant,
                "feedback_dict":         feedback_dict,
                "observation_context":   {
                    "synthetic": True,
                    "source_feedback_id": syn.source_feedback_id,
                    "quality_score": syn.quality_score,
                },
            },
            timeout=10.0,
        )
    except Exception as exc:
        logger.warning("Could not push synthetic example to MS-013: %s", exc)
