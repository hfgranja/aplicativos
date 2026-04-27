from sqlalchemy import Boolean, Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from pec_shared.models_base import Base


class FeedbackStyleModel(Base):
    __tablename__ = "feedback_styles"

    id                   = Column(String, primary_key=True)
    name                 = Column(String(200), nullable=False)
    description          = Column(Text, nullable=False)
    tone                 = Column(String(50), nullable=False)
    template_prompt      = Column(Text, nullable=False)
    example_strengths    = Column(Text, nullable=False)   # JSON array stored as text
    example_improvements = Column(Text, nullable=False)   # JSON array stored as text
    is_active            = Column(Boolean, default=True)
    is_default           = Column(Boolean, default=False)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())
