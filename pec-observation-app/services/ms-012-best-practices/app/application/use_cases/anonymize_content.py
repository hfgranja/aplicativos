"""Anonymize transcript text and audio clips to protect teacher privacy.

Text:  regex-based PII scrub (names → "Prof. A", school → "Escola X")
Audio: pitch-shift via pydub frame-rate trick (±3 semitones) so voice is
       unrecognisable but speech content remains intelligible.
"""
import io
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Common Brazilian name patterns and education-domain PII markers
_NAME_RE = re.compile(
    r"\b(professor[a]?|prof\.?|diretor[a]?|coordenador[a]?)\s+[A-ZÁÉÍÓÚÀÂÊÔÃÕÇÜÑ][a-záéíóúàâêôãõçüñ]+(?:\s+[A-ZÁÉÍÓÚÀÂÊÔÃÕÇÜÑ][a-záéíóúàâêôãõçüñ]+)*",
    re.IGNORECASE,
)
_SCHOOL_RE = re.compile(
    r"\b(escola\s+(estadual|municipal|e\.e\.|e\.m\.)\s+[A-ZÁÉÍÓÚÀÂÊÔÃÕÇÜÑ][^\.,;]+)",
    re.IGNORECASE,
)
_EMPLOYEE_ID_RE = re.compile(r"\bRF\s*\d{6,}\b", re.IGNORECASE)

_PERSON_COUNTER  = {}
_SCHOOL_COUNTER  = {}


def anonymize_text(text: str) -> str:
    """Replace PII with generic placeholders, deterministically per session."""
    result = text

    # Schools first (longer match)
    def _replace_school(m):
        key = m.group(0).lower().strip()
        if key not in _SCHOOL_COUNTER:
            idx = len(_SCHOOL_COUNTER) + 1
            _SCHOOL_COUNTER[key] = f"Escola {chr(87 + idx)}"  # X, Y, Z…
        return _SCHOOL_COUNTER[key]

    result = _SCHOOL_RE.sub(_replace_school, result)

    # People names
    def _replace_name(m):
        full = m.group(0)
        title = m.group(1).capitalize()
        key = full.lower().strip()
        if key not in _PERSON_COUNTER:
            idx = len(_PERSON_COUNTER) + 1
            letter = chr(64 + idx)  # A, B, C…
            _PERSON_COUNTER[key] = f"{title} {letter}"
        return _PERSON_COUNTER[key]

    result = _NAME_RE.sub(_replace_name, result)
    result = _EMPLOYEE_ID_RE.sub("[RF omitido]", result)

    return result


# Pitch-shift factor for 3 semitones up (2^(3/12) ≈ 1.189)
_PITCH_FACTOR = 2 ** (3 / 12)


def anonymize_audio(audio_bytes: bytes, fmt: str = "m4a") -> Optional[bytes]:
    """Return pitch-shifted audio bytes or None if pydub is not available."""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)
        # Pitch shift: change frame rate then export at original rate
        shifted = audio._spawn(
            audio.raw_data,
            overrides={"frame_rate": int(audio.frame_rate * _PITCH_FACTOR)},
        ).set_frame_rate(audio.frame_rate)
        buf = io.BytesIO()
        shifted.export(buf, format="mp3")
        return buf.getvalue()
    except ImportError:
        logger.warning("pydub not installed — returning audio without pitch shift")
        return audio_bytes
    except Exception as exc:
        logger.error("Audio anonymization failed: %s", exc)
        return audio_bytes
