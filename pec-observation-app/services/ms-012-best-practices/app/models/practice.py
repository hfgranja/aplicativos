from sqlalchemy import Column, String, Text, Integer
from pec_shared.models_base import Base


class BestPracticeCardModel(Base):
    __tablename__ = "best_practice_cards"

    id                    = Column(String, primary_key=True)
    title                 = Column(String(300), nullable=False)
    criterion             = Column(String(50),  nullable=False)
    subject               = Column(String(100), nullable=False)
    grade                 = Column(String(50),  nullable=False)
    excerpt               = Column(Text, nullable=False)
    ai_explanation        = Column(Text, nullable=False)
    audio_clip_key        = Column(String(300), nullable=True)
    # Anime-style practice video
    video_key             = Column(String(300), nullable=True)
    video_status          = Column(String(20),  default="pending")  # pending|processing|ready|failed
    video_duration_s      = Column(Integer,     nullable=True)
    rubric_alignment      = Column(Text, default="[]")   # JSON list
    tags                  = Column(Text, default="[]")   # JSON list
    status                = Column(String(20), default="draft", nullable=False)
    source_observation_id = Column(String, nullable=False)
    created_by_pec_id     = Column(String, nullable=False)
    published_at          = Column(String, nullable=True)
    created_at            = Column(String, nullable=False)


class DistributionModel(Base):
    __tablename__ = "practice_distributions"

    id          = Column(String, primary_key=True)
    card_id     = Column(String, nullable=False, index=True)
    teacher_id  = Column(String, nullable=False, index=True)
    sent_by_pec = Column(String, nullable=False)
    message     = Column(Text, default="")
    sent_at     = Column(String, nullable=False)
    viewed_at   = Column(String, nullable=True)
