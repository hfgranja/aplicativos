"""Video assembly pipeline.

Combines Pillow anime frames + anonymised audio into an MP4 video.

Flow
────
1. frames_for_card()        → [(PIL Image, duration_s), ...]
2. _frames_to_clips()       → list[ImageClip] with crossfade transitions
3. _attach_audio()          → CompositeVideoClip with AudioFileClip
4. clip.write_videofile()   → MP4 bytes
5. upload_video()           → MinIO key
"""
from __future__ import annotations

import io
import logging
import os
import tempfile
from typing import Optional

import numpy as np

from .generate_anime_frames import frames_for_card
from ...adapters.storage.minio_adapter import upload_video, BUCKET

logger = logging.getLogger(__name__)


def _pil_to_numpy(img) -> np.ndarray:
    return np.array(img.convert("RGB"))


def build_video(
    card_data: dict,
    audio_bytes: Optional[bytes],
    output_key: str,
) -> tuple[str, int]:
    """Generate an anime-style video for *card_data*.

    Returns (minio_key, duration_seconds).
    Raises RuntimeError on failure.
    """
    try:
        from moviepy.editor import (
            ImageClip, AudioFileClip, CompositeVideoClip,
            concatenate_videoclips,
        )
    except ImportError as exc:
        raise RuntimeError(f"moviepy not available: {exc}")

    frames = frames_for_card(card_data)
    if not frames:
        raise RuntimeError("No frames generated")

    clips = []
    for img, dur in frames:
        arr  = _pil_to_numpy(img)
        clip = ImageClip(arr).set_duration(dur)
        clip = clip.crossfadein(0.4)
        clips.append(clip)

    video_clip = concatenate_videoclips(clips, method="compose", padding=-0.4)
    total_duration = video_clip.duration

    # Attach audio (loop if shorter than video, trim if longer)
    if audio_bytes:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_bytes)
            audio_path = tmp.name
        try:
            audio = AudioFileClip(audio_path)
            if audio.duration < total_duration:
                # Repeat audio to fill
                repeats = int(total_duration / audio.duration) + 1
                from moviepy.editor import concatenate_audioclips
                audio = concatenate_audioclips([audio] * repeats)
            audio = audio.subclip(0, total_duration)
            video_clip = video_clip.set_audio(audio)
        except Exception as exc:
            logger.warning("Could not attach audio: %s", exc)
        finally:
            os.unlink(audio_path)

    # Render to bytes
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as out:
        out_path = out.name

    try:
        video_clip.write_videofile(
            out_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="fast",
            logger=None,          # suppress moviepy progress bars
            ffmpeg_params=["-crf", "28"],
        )
        with open(out_path, "rb") as f:
            video_bytes = f.read()
    finally:
        os.unlink(out_path)

    upload_video(output_key, video_bytes)
    logger.info("Video uploaded: %s (%.1f s, %.2f MB)",
                output_key, total_duration, len(video_bytes) / 1e6)
    return output_key, int(total_duration)
