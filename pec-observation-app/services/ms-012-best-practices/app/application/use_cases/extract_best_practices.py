"""Extract BestPracticeCard candidates from an approved feedback payload.

Input:  structured feedback JSON (from MS-006/MS-007) + observation metadata
Output: list[BestPracticeCard] saved as DRAFT, ready for PEC review

Each approved "strength" item with a non-trivial evidence excerpt becomes one
candidate card. Audio clip extraction is attempted if segment timestamps are
available from the transcription.
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from ..use_cases.anonymize_content import anonymize_text, anonymize_audio
from ...domain.best_practice import (
    BestPracticeCard, PracticeStatus, PedagogicalCriterion,
)

logger = logging.getLogger(__name__)

# Map feedback categories → SEDUC criteria
_CRITERION_MAP = {
    "planejamento": PedagogicalCriterion.PLANEJAMENTO,
    "didática":     PedagogicalCriterion.DIDATICA,
    "clareza":      PedagogicalCriterion.DIDATICA,
    "engajamento":  PedagogicalCriterion.ENGAJAMENTO,
    "avaliação":    PedagogicalCriterion.AVALIACAO,
    "gestão":       PedagogicalCriterion.GESTAO,
    "tempo":        PedagogicalCriterion.GESTAO,
}

def _infer_criterion(title: str, description: str) -> PedagogicalCriterion:
    text = (title + " " + description).lower()
    for keyword, criterion in _CRITERION_MAP.items():
        if keyword in text:
            return criterion
    return PedagogicalCriterion.DIDATICA


def _rubric_items(criterion: PedagogicalCriterion) -> list[str]:
    return {
        PedagogicalCriterion.PLANEJAMENTO: [
            "Alinhamento com o Currículo Paulista",
            "Objetivos de aprendizagem claros",
        ],
        PedagogicalCriterion.DIDATICA: [
            "Clareza nas explicações",
            "Uso de exemplos contextualizados",
            "Sequência didática coerente",
        ],
        PedagogicalCriterion.ENGAJAMENTO: [
            "Participação ativa dos estudantes",
            "Estratégias de motivação",
        ],
        PedagogicalCriterion.AVALIACAO: [
            "Verificação da compreensão",
            "Feedback imediato aos estudantes",
        ],
        PedagogicalCriterion.GESTAO: [
            "Aproveitamento eficiente do tempo",
            "Transições ágeis entre atividades",
        ],
    }[criterion]


def extract_cards(
    observation_id: str,
    pec_id: str,
    subject: str,
    grade: str,
    feedback: dict,
    audio_bytes: Optional[bytes] = None,
    segments: Optional[list[dict]] = None,
) -> list[BestPracticeCard]:
    """Return a list of BestPracticeCard (DRAFT) from feedback strengths."""
    strengths = feedback.get("strengths", [])
    cards     = []
    now       = datetime.now(timezone.utc).isoformat()

    for strength in strengths:
        title       = strength.get("title", "Boa prática identificada")
        description = strength.get("description", "")
        evidence    = strength.get("evidence", "")

        if len(evidence) < 20:
            # Evidence too short — skip, not meaningful enough
            continue

        criterion    = _infer_criterion(title, description)
        anon_excerpt = anonymize_text(evidence)
        anon_title   = anonymize_text(title)
        ai_explanation = (
            f"{anonymize_text(description)}\n\n"
            f"Esta prática demonstra alinhamento com o critério SEDUC: "
            f"{criterion.display}."
        )

        audio_key: Optional[str] = None
        if audio_bytes and segments:
            audio_key = _extract_audio_clip(
                observation_id, title, audio_bytes, segments, evidence
            )

        card = BestPracticeCard(
            id                    = str(uuid.uuid4()),
            title                 = anon_title,
            criterion             = criterion,
            subject               = subject,
            grade                 = grade,
            excerpt               = anon_excerpt,
            ai_explanation        = ai_explanation,
            audio_clip_key        = audio_key,
            rubric_alignment      = _rubric_items(criterion),
            status                = PracticeStatus.DRAFT,
            source_observation_id = observation_id,
            created_by_pec_id     = pec_id,
            created_at            = now,
            tags                  = [subject, grade, criterion.value],
        )
        cards.append(card)

    logger.info("Extracted %d best-practice candidates from obs %s", len(cards), observation_id)
    return cards


def _extract_audio_clip(
    obs_id: str,
    strength_title: str,
    audio_bytes: bytes,
    segments: list[dict],
    evidence_text: str,
) -> Optional[str]:
    """Find the segment(s) containing the evidence excerpt, anonymize and
    return the MinIO key where the clip was stored."""
    try:
        from ...adapters.storage.minio_adapter import upload_practice_clip

        # Find closest segment by text similarity (simple substring match)
        matched_segments = [
            s for s in segments
            if any(word in s.get("text", "") for word in evidence_text.split()[:5])
        ]
        if not matched_segments:
            return None

        start = matched_segments[0].get("start", 0.0)
        end   = matched_segments[-1].get("end", start + 30.0)

        # Clip audio
        clipped = _clip_audio(audio_bytes, start, end)
        if clipped is None:
            return None

        anon_audio = anonymize_audio(clipped)
        key = f"best-practices/{obs_id}/{uuid.uuid4()}.mp3"
        upload_practice_clip(key, anon_audio)
        return key
    except Exception as exc:
        logger.warning("Audio clip extraction failed: %s", exc)
        return None


def _clip_audio(audio_bytes: bytes, start_s: float, end_s: float) -> Optional[bytes]:
    try:
        import io
        from pydub import AudioSegment
        audio   = AudioSegment.from_file(io.BytesIO(audio_bytes))
        clipped = audio[int(start_s * 1000): int(end_s * 1000)]
        buf     = io.BytesIO()
        clipped.export(buf, format="mp3")
        return buf.getvalue()
    except Exception as exc:
        logger.warning("Audio clip failed: %s", exc)
        return None
