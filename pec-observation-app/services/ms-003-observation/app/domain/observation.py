"""Core domain entity for Observation — pure Python, no infrastructure dependencies."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class ObservationStatus(str, Enum):
    DRAFT = "DRAFT"
    READY_TO_RECORD = "READY_TO_RECORD"
    RECORDED = "RECORDED"
    AUDIO_UPLOADED = "AUDIO_UPLOADED"
    TRANSCRIBING = "TRANSCRIBING"
    TRANSCRIBED = "TRANSCRIBED"
    GENERATING_FEEDBACK = "GENERATING_FEEDBACK"
    FEEDBACK_READY = "FEEDBACK_READY"
    IN_REVIEW = "IN_REVIEW"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    APPROVED = "APPROVED"


# Hard-coded valid forward transitions per SDD
VALID_TRANSITIONS: dict[ObservationStatus, list[ObservationStatus]] = {
    ObservationStatus.DRAFT: [ObservationStatus.READY_TO_RECORD],
    ObservationStatus.READY_TO_RECORD: [ObservationStatus.RECORDED, ObservationStatus.DRAFT],
    ObservationStatus.RECORDED: [ObservationStatus.AUDIO_UPLOADED],
    ObservationStatus.AUDIO_UPLOADED: [ObservationStatus.TRANSCRIBING],
    ObservationStatus.TRANSCRIBING: [ObservationStatus.TRANSCRIBED, ObservationStatus.RECORDED],
    ObservationStatus.TRANSCRIBED: [ObservationStatus.GENERATING_FEEDBACK],
    ObservationStatus.GENERATING_FEEDBACK: [ObservationStatus.FEEDBACK_READY, ObservationStatus.TRANSCRIBED],
    ObservationStatus.FEEDBACK_READY: [ObservationStatus.IN_REVIEW],
    ObservationStatus.IN_REVIEW: [ObservationStatus.HUMAN_REVIEWED],
    ObservationStatus.HUMAN_REVIEWED: [ObservationStatus.APPROVED],
    ObservationStatus.APPROVED: [],
}


class DomainError(Exception):
    pass


@dataclass
class ObservationDomain:
    id: str
    school_id: str
    teacher_id: str
    subject: str
    grade: str
    lesson_theme: str
    lesson_objectives: str
    status: ObservationStatus
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    audio_local_path: Optional[str] = None
    audio_minio_key: Optional[str] = None
    audio_duration_seconds: Optional[int] = None
    audio_checksum: Optional[str] = None

    def is_ready_for_recording(self) -> bool:
        return bool(self.school_id and self.teacher_id and
                    self.subject and self.grade and self.lesson_theme)

    def transition_to(self, new_status: ObservationStatus, by: str = "") -> None:
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise DomainError(
                f"Invalid transition: {self.status.value} → {new_status.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        self.status = new_status
