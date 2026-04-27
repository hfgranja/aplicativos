"""MS-013 Learning Engine — embeddings, RAG, continuous model improvement."""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from sqlalchemy import text

from app.adapters.api.router import router
from app.adapters.events.consumer import start_consumer
from app.application.use_cases.ingest_feedback import ingest_approved_feedback
from app.application.use_cases.ingest_knowledge import ingest_crawl_page, ingest_knowledge_document
from app.application.use_cases.rebuild_model import maybe_rebuild
from app.config import settings
from app.models.embedding import EmbeddingRecord, ModelBuild
from pec_shared.models_base import Base, engine, SessionLocal
from pec_shared.telemetry import init_telemetry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ms-013")

app = FastAPI(title="PEC Learning Engine", version="1.0.0")
app.include_router(router)

init_telemetry(settings.service_name, settings.environment, settings.otel_exporter_enabled)


@app.on_event("startup")
async def startup():
    # Create pgvector extension then tables
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready")

    # Start Redis event consumer
    start_consumer(_handle_event)

    # Scheduled nightly model rebuild (checks threshold, rebuilds only if needed)
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _scheduled_rebuild,
        trigger="cron",
        hour=2,
        minute=0,
        id="nightly-rebuild",
    )
    scheduler.start()
    logger.info("Nightly rebuild scheduler started")


def _handle_event(event_type: str, payload: dict) -> None:
    db = SessionLocal()
    try:
        if event_type in ("knowledge.document.created", "knowledge.document.updated",
                          "crawl.page.scraped"):
            ingest_knowledge_document(
                db=db,
                doc_id=payload.get("doc_id") or payload.get("id", ""),
                title=payload.get("title", ""),
                content=payload.get("content") or payload.get("text", ""),
                source_url=payload.get("source_url") or payload.get("url", ""),
            )

        elif event_type == "feedback.human_approved":
            total = ingest_approved_feedback(
                db=db,
                feedback_id=payload.get("feedback_id", ""),
                transcription_snippet=payload.get("transcription_text", ""),
                feedback_dict=payload.get("feedback_content", {}),
                observation_context=payload.get("observation_context", {}),
            )
            # Trigger rebuild if threshold reached
            if total % settings.rebuild_threshold == 0:
                maybe_rebuild(db)

        elif event_type in ("best_practice.created", "best_practice.updated"):
            from app.adapters.embedding.ollama_embedding import embed
            from app.adapters.vector_store.pgvector_store import upsert_embedding
            content = payload.get("content", "")
            if content:
                try:
                    vec = embed(content[:6000], settings.ollama_base_url,
                                settings.ollama_embedding_model)
                    upsert_embedding(
                        db=db,
                        source_type="best_practice",
                        source_id=payload.get("id", ""),
                        content=content[:6000],
                        embedding=vec,
                        metadata={"title": payload.get("title", "")},
                    )
                except Exception as exc:
                    logger.warning("Could not embed best practice: %s", exc)
    finally:
        db.close()


def _scheduled_rebuild() -> None:
    db = SessionLocal()
    try:
        maybe_rebuild(db)
    finally:
        db.close()


@app.get("/health")
def health():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "ms-013-learning"}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}
    finally:
        db.close()
