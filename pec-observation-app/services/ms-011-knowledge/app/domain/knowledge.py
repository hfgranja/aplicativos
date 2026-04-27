from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class DocumentType(str, Enum):
    SEDUC_POLICY      = "seduc_policy"
    CURRICULUM_GUIDE  = "curriculum_guide"
    EVALUATION_RUBRIC = "evaluation_rubric"
    FEEDBACK_EXAMPLE  = "feedback_example"
    OTHER             = "other"


class StyleTone(str, Enum):
    FORMAL       = "formal"
    CONSTRUCTIVE = "constructive"
    DIRECT       = "direct"
    SUPPORTIVE   = "supportive"


@dataclass
class DocumentChunk:
    chunk_index: int
    text: str
    char_start: int
    char_end: int


@dataclass
class KnowledgeDocument:
    id: str
    title: str
    document_type: DocumentType
    source_filename: str
    full_text: str
    chunks: list[DocumentChunk]
    chunk_count: int
    uploaded_by: str
    is_active: bool
    created_at: datetime
    description: Optional[str] = None


@dataclass
class FeedbackStyle:
    id: str
    name: str
    description: str
    tone: StyleTone
    template_prompt: str          # injected into LLM system prompt
    example_strengths: list[str]
    example_improvements: list[str]
    is_active: bool
    is_default: bool
    created_at: datetime


@dataclass
class ContextResult:
    """Relevant chunks returned to MS-006 for a given observation."""
    chunks: list[str]
    document_titles: list[str]
    active_style: Optional[FeedbackStyle]
