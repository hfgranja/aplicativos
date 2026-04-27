"""faster-whisper adapter — same params as teacher-feedback/backend/services/."""
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from pec_shared.text_optimizer import optimize, optimization_report

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionSegment:
    start: float
    end: float
    text: str
    speaker: str = "unknown"


@dataclass
class TranscriptionResult:
    text: str
    segments: List[TranscriptionSegment]
    language: str
    duration_seconds: float
    model_used: str
    average_confidence: Optional[float] = None
    optimized_text: Optional[str] = None
    token_report: Optional[dict] = None


_model = None


def _get_model(model_size: str, device: str, compute_type: str):
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        logger.info("Loading Whisper model %s (%s/%s)...", model_size, device, compute_type)
        _model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info("Whisper model loaded.")
    return _model


def transcribe(
    file_path: str,
    model_size: str = "small",
    device: str = "cpu",
    compute_type: str = "int8",
    language: str = "pt",
    beam_size: int = 5,
    max_tokens: int = 3500,
) -> TranscriptionResult:
    model = _get_model(model_size, device, compute_type)
    segments_raw, info = model.transcribe(
        file_path, language=language, beam_size=beam_size
    )
    segments = []
    full_text_parts = []
    for seg in segments_raw:
        segments.append(TranscriptionSegment(
            start=seg.start, end=seg.end, text=seg.text.strip()
        ))
        full_text_parts.append(seg.text.strip())

    raw_text = " ".join(full_text_parts)
    optimized = optimize(raw_text, max_tokens=max_tokens)
    report = optimization_report(raw_text, optimized)
    logger.info(
        "Text optimization: %d → %d estimated tokens (%.1f%% reduction)",
        report["estimated_tokens_before"],
        report["estimated_tokens_after"],
        report["reduction_pct"],
    )

    return TranscriptionResult(
        text=raw_text,
        segments=segments,
        language=info.language,
        duration_seconds=info.duration if hasattr(info, "duration") else 0.0,
        model_used=f"whisper-{model_size}",
        optimized_text=optimized,
        token_report=report,
    )
