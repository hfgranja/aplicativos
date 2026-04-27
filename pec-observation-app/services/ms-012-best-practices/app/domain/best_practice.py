"""Domain entities for MS-012 Best Practices."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PracticeStatus(str, Enum):
    DRAFT     = "draft"       # Extracted, awaiting PEC review
    PUBLISHED = "published"   # Visible in library
    ARCHIVED  = "archived"    # Soft-deleted


class PedagogicalCriterion(str, Enum):
    PLANEJAMENTO = "planejamento"
    DIDATICA     = "didatica"
    ENGAJAMENTO  = "engajamento"
    AVALIACAO    = "avaliacao"
    GESTAO       = "gestao"

    @property
    def display(self) -> str:
        return {
            "planejamento": "Planejamento e alinhamento curricular",
            "didatica":     "Clareza didática e condução da aula",
            "engajamento":  "Engajamento dos estudantes",
            "avaliacao":    "Avaliação formativa",
            "gestao":       "Gestão do tempo",
        }[self.value]


@dataclass
class BestPracticeCard:
    id:                    str
    title:                 str
    criterion:             PedagogicalCriterion
    subject:               str
    grade:                 str
    excerpt:               str          # Anonymized transcript excerpt
    ai_explanation:        str          # Why this is a best practice
    audio_clip_key:        Optional[str]  # MinIO object key for anon. audio
    rubric_alignment:      list[str]    # SEDUC rubric items this exemplifies
    status:                PracticeStatus
    source_observation_id: str
    created_by_pec_id:     str
    created_at:            str
    published_at:          Optional[str] = None
    tags:                  list[str] = field(default_factory=list)


@dataclass
class Distribution:
    id:          str
    card_id:     str
    teacher_id:  str
    sent_by_pec: str
    message:     str
    sent_at:     str
    viewed_at:   Optional[str] = None
