import os
from typing import Optional


def transcribe_audio(file_path: str) -> Optional[str]:
    """Transcribe audio/video file using faster-whisper."""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("small", device="cpu", compute_type="int8")
        segments, info = model.transcribe(file_path, beam_size=5, language="pt")
        text = " ".join(segment.text.strip() for segment in segments)
        return text
    except ImportError:
        return None
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")
