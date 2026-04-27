"""REST API for the Learning Engine (called by MS-006 and MS-011)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.use_cases.ingest_feedback import ingest_approved_feedback
from app.application.use_cases.ingest_knowledge import ingest_crawl_page, ingest_knowledge_document
from app.application.use_cases.rag_query import retrieve_context
from app.application.use_cases.rebuild_model import maybe_rebuild
from app.config import settings
from pec_shared.models_base import get_db

router = APIRouter(prefix="/api/v1/learning")


# ── RAG query ─────────────────────────────────────────────────────────────────

class ContextRequest(BaseModel):
    query: str
    source_types: list[str] | None = None
    limit: int = 6


class ContextChunk(BaseModel):
    source_type: str
    source_id: str
    content: str
    metadata: dict = {}


class ContextResponse(BaseModel):
    chunks: list[ContextChunk]
    model_name: str


@router.post("/context", response_model=ContextResponse)
def get_context(req: ContextRequest, db: Session = Depends(get_db)):
    chunks = retrieve_context(db, req.query, req.source_types, req.limit)
    return ContextResponse(
        chunks=[ContextChunk(**c) for c in chunks],
        model_name=settings.pec_model_name,
    )


# ── Ingest endpoints ──────────────────────────────────────────────────────────

class IngestDocRequest(BaseModel):
    doc_id: str
    title: str
    content: str
    source_url: str = ""
    extra_meta: dict = {}


@router.post("/ingest/document", status_code=202)
def ingest_document(req: IngestDocRequest, db: Session = Depends(get_db)):
    ingest_knowledge_document(
        db, req.doc_id, req.title, req.content, req.source_url, req.extra_meta
    )
    return {"status": "queued", "doc_id": req.doc_id}


class IngestPageRequest(BaseModel):
    url: str
    title: str
    text: str


@router.post("/ingest/page", status_code=202)
def ingest_page(req: IngestPageRequest, db: Session = Depends(get_db)):
    ingest_crawl_page(db, req.url, req.title, req.text)
    return {"status": "queued", "url": req.url}


class IngestFeedbackRequest(BaseModel):
    feedback_id: str
    transcription_snippet: str
    feedback_dict: dict
    observation_context: dict = {}


@router.post("/ingest/feedback", status_code=202)
def ingest_feedback(req: IngestFeedbackRequest, db: Session = Depends(get_db)):
    total = ingest_approved_feedback(
        db,
        req.feedback_id,
        req.transcription_snippet,
        req.feedback_dict,
        req.observation_context,
    )
    return {"status": "queued", "feedback_id": req.feedback_id, "total_examples": total}


# ── Model management ──────────────────────────────────────────────────────────

@router.post("/model/rebuild", status_code=202)
def trigger_rebuild(force: bool = False, db: Session = Depends(get_db)):
    build = maybe_rebuild(db, force=force)
    if build is None:
        return {"status": "skipped", "reason": "not enough new examples"}
    return {"status": build.status, "build_id": str(build.id), "examples": build.examples_count}


@router.get("/model/status")
def model_status(db: Session = Depends(get_db)):
    from app.models.embedding import ModelBuild
    from app.adapters.vector_store.pgvector_store import count_by_type
    last = (
        db.query(ModelBuild)
        .order_by(ModelBuild.created_at.desc())
        .first()
    )
    return {
        "pec_model_name": settings.pec_model_name,
        "base_model": settings.ollama_model,
        "knowledge_docs": count_by_type(db, "knowledge_document"),
        "approved_feedbacks": count_by_type(db, "approved_feedback"),
        "best_practices": count_by_type(db, "best_practice"),
        "last_build": {
            "status": last.status if last else None,
            "examples": last.examples_count if last else 0,
            "built_at": last.built_at.isoformat() if last and last.built_at else None,
        },
    }
