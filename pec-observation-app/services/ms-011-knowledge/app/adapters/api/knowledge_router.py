"""MS-011 Knowledge Base API — document ingestion + feedback styles."""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.use_cases.ingest_document import IngestDocumentUseCase, IngestInput
from app.database import get_db
from app.domain.knowledge import DocumentType, StyleTone
from app.models.document import DocumentChunkModel, KnowledgeDocumentModel
from app.models.feedback_style import FeedbackStyleModel
from pec_shared.models_base import gen_uuid
from pec_shared.security import decode_token
from app.config import settings

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])
_ingest = IngestDocumentUseCase()


# ── Auth helper ──────────────────────────────────────────────────────────────

def _current_user(authorization: str = "") -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        return decode_token(authorization[7:], settings.SECRET_KEY)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# ── Request / Response schemas ───────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: str
    title: str
    document_type: str
    source_filename: str
    description: Optional[str]
    chunk_count: int
    uploaded_by: str
    is_active: bool
    created_at: str


class FeedbackStyleIn(BaseModel):
    name: str
    description: str
    tone: StyleTone = StyleTone.CONSTRUCTIVE
    template_prompt: str
    example_strengths: list[str] = []
    example_improvements: list[str] = []
    is_default: bool = False


class FeedbackStyleResponse(BaseModel):
    id: str
    name: str
    description: str
    tone: str
    template_prompt: str
    example_strengths: list[str]
    example_improvements: list[str]
    is_active: bool
    is_default: bool
    created_at: str


class ContextResponse(BaseModel):
    chunks: list[str]
    document_titles: list[str]
    active_style: Optional[FeedbackStyleResponse]


# ── Documents ────────────────────────────────────────────────────────────────

@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: DocumentType = Form(DocumentType.OTHER),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:  # 20 MB
        raise HTTPException(status_code=413, detail="File too large (max 20 MB)")

    try:
        doc = _ingest.execute(IngestInput(
            title           = title,
            document_type   = document_type,
            source_filename = file.filename or "upload",
            raw_bytes       = raw,
            content_type    = file.content_type or "text/plain",
            uploaded_by     = "api",
            description     = description,
        ))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    db_doc = KnowledgeDocumentModel(
        id              = doc.id,
        title           = doc.title,
        document_type   = doc.document_type.value,
        source_filename = doc.source_filename,
        description     = doc.description,
        full_text       = doc.full_text,
        chunk_count     = doc.chunk_count,
        uploaded_by     = doc.uploaded_by,
        is_active       = True,
    )
    db.add(db_doc)

    for chunk in doc.chunks:
        db.add(DocumentChunkModel(
            document_id = doc.id,
            chunk_index = chunk.chunk_index,
            text        = chunk.text,
            char_start  = chunk.char_start,
            char_end    = chunk.char_end,
        ))

    db.commit()
    db.refresh(db_doc)
    return _doc_response(db_doc)


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(
    document_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(KnowledgeDocumentModel).filter(KnowledgeDocumentModel.is_active == True)
    if document_type:
        q = q.filter(KnowledgeDocumentModel.document_type == document_type)
    return [_doc_response(d) for d in q.order_by(KnowledgeDocumentModel.created_at.desc()).all()]


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDocumentModel).filter_by(id=doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return _doc_response(doc)


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDocumentModel).filter_by(id=doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.is_active = False
    db.commit()


# ── Feedback Styles ──────────────────────────────────────────────────────────

@router.post("/feedback-styles", response_model=FeedbackStyleResponse, status_code=201)
def create_style(payload: FeedbackStyleIn, db: Session = Depends(get_db)):
    if payload.is_default:
        db.query(FeedbackStyleModel).update({"is_default": False})

    style = FeedbackStyleModel(
        id                   = str(uuid.uuid4()),
        name                 = payload.name,
        description          = payload.description,
        tone                 = payload.tone.value,
        template_prompt      = payload.template_prompt,
        example_strengths    = json.dumps(payload.example_strengths, ensure_ascii=False),
        example_improvements = json.dumps(payload.example_improvements, ensure_ascii=False),
        is_active            = True,
        is_default           = payload.is_default,
    )
    db.add(style)
    db.commit()
    db.refresh(style)
    return _style_response(style)


@router.get("/feedback-styles", response_model=list[FeedbackStyleResponse])
def list_styles(db: Session = Depends(get_db)):
    styles = db.query(FeedbackStyleModel).filter_by(is_active=True)\
               .order_by(FeedbackStyleModel.is_default.desc()).all()
    return [_style_response(s) for s in styles]


@router.patch("/feedback-styles/{style_id}", response_model=FeedbackStyleResponse)
def update_style(style_id: str, payload: FeedbackStyleIn, db: Session = Depends(get_db)):
    style = db.query(FeedbackStyleModel).filter_by(id=style_id).first()
    if not style:
        raise HTTPException(status_code=404, detail="Style not found")

    if payload.is_default:
        db.query(FeedbackStyleModel).update({"is_default": False})

    style.name                 = payload.name
    style.description          = payload.description
    style.tone                 = payload.tone.value
    style.template_prompt      = payload.template_prompt
    style.example_strengths    = json.dumps(payload.example_strengths, ensure_ascii=False)
    style.example_improvements = json.dumps(payload.example_improvements, ensure_ascii=False)
    style.is_default           = payload.is_default
    db.commit()
    db.refresh(style)
    return _style_response(style)


@router.delete("/feedback-styles/{style_id}", status_code=204)
def delete_style(style_id: str, db: Session = Depends(get_db)):
    style = db.query(FeedbackStyleModel).filter_by(id=style_id).first()
    if not style:
        raise HTTPException(status_code=404, detail="Style not found")
    style.is_active = False
    db.commit()


# ── Context query (internal, called by MS-006) ───────────────────────────────

@router.get("/context", response_model=ContextResponse)
def get_context(
    subject: Optional[str] = Query(None),
    grade: Optional[str] = Query(None),
    max_chunks: int = Query(5, le=20),
    style_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Return relevant document chunks + active feedback style for MS-006."""
    keywords = " ".join(filter(None, [subject, grade])).lower()

    chunks_q = db.query(DocumentChunkModel).join(
        KnowledgeDocumentModel,
        DocumentChunkModel.document_id == KnowledgeDocumentModel.id,
    ).filter(KnowledgeDocumentModel.is_active == True)

    if keywords:
        chunks_q = chunks_q.filter(
            DocumentChunkModel.text.ilike(f"%{keywords.split()[0]}%")
            if keywords.split() else True
        )

    db_chunks = chunks_q.limit(max_chunks).all()
    chunk_texts  = [c.text for c in db_chunks]
    doc_ids      = list({c.document_id for c in db_chunks})
    doc_titles   = [
        d.title for d in
        db.query(KnowledgeDocumentModel.title)
          .filter(KnowledgeDocumentModel.id.in_(doc_ids)).all()
    ] if doc_ids else []

    # Resolve style
    if style_id:
        style_obj = db.query(FeedbackStyleModel).filter_by(id=style_id, is_active=True).first()
    else:
        style_obj = db.query(FeedbackStyleModel).filter_by(is_default=True, is_active=True).first()

    return ContextResponse(
        chunks          = chunk_texts,
        document_titles = doc_titles,
        active_style    = _style_response(style_obj) if style_obj else None,
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

def _doc_response(d: KnowledgeDocumentModel) -> DocumentResponse:
    return DocumentResponse(
        id              = d.id,
        title           = d.title,
        document_type   = d.document_type,
        source_filename = d.source_filename,
        description     = d.description,
        chunk_count     = d.chunk_count,
        uploaded_by     = d.uploaded_by,
        is_active       = d.is_active,
        created_at      = d.created_at.isoformat() if d.created_at else "",
    )


def _style_response(s: FeedbackStyleModel) -> FeedbackStyleResponse:
    return FeedbackStyleResponse(
        id                   = s.id,
        name                 = s.name,
        description          = s.description,
        tone                 = s.tone,
        template_prompt      = s.template_prompt,
        example_strengths    = json.loads(s.example_strengths or "[]"),
        example_improvements = json.loads(s.example_improvements or "[]"),
        is_active            = s.is_active,
        is_default           = s.is_default,
        created_at           = s.created_at.isoformat() if s.created_at else "",
    )
