from fastapi import FastAPI
from pec_shared.telemetry import init_telemetry
from app.config import settings
from app.database import SessionLocal
from app.models.document import KnowledgeDocumentModel, DocumentChunkModel
from app.models.feedback_style import FeedbackStyleModel
from app.models.crawl_log import CrawlLogModel  # noqa: F401 — ensures table is created
from app.adapters.api.knowledge_router import router as knowledge_router
from app.adapters.scheduler.seduc_crawler import start_scheduler, stop_scheduler, run_crawl
from pec_shared.models_base import Base
from sqlalchemy import create_engine
import json, uuid

init_telemetry(settings.SERVICE_NAME, enabled=settings.OTEL_EXPORTER_ENABLED)

app = FastAPI(title="MS-011 Knowledge Base", version="1.0.0")
app.include_router(knowledge_router)


@app.on_event("startup")
def startup():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    _seed_default_style()
    start_scheduler(run_hour=settings.CRAWLER_HOUR, run_minute=settings.CRAWLER_MINUTE)


def _seed_default_style():
    db = SessionLocal()
    try:
        if db.query(FeedbackStyleModel).count() == 0:
            db.add(FeedbackStyleModel(
                id          = str(uuid.uuid4()),
                name        = "SEDUC Padrão",
                description = "Estilo oficial SEDUC-SP: equilibrado, construtivo, baseado em evidências",
                tone        = "constructive",
                template_prompt = (
                    "Use linguagem respeitosa e profissional. "
                    "Baseie cada ponto em evidências concretas observadas na aula. "
                    "Equilibre pontos fortes e pontos de desenvolvimento. "
                    "Siga as diretrizes pedagógicas da SEDUC-SP."
                ),
                example_strengths    = json.dumps(["O professor demonstrou domínio do conteúdo ao explicar as frações com exemplos do cotidiano."]),
                example_improvements = json.dumps(["Recomenda-se ampliar o tempo de atividade prática para consolidar o aprendizado conceitual."]),
                is_active  = True,
                is_default = True,
            ))
            db.commit()
    finally:
        db.close()


@app.on_event("shutdown")
def shutdown():
    stop_scheduler()


@app.get("/health")
def health():
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.post("/api/v1/crawler/run", tags=["crawler"])
def trigger_crawl():
    """Manually trigger a SEDUC crawl cycle (useful for testing)."""
    result = run_crawl()
    return {"status": "done", **result}


@app.get("/api/v1/crawler/log", tags=["crawler"])
def crawl_log(limit: int = 50):
    """Return recent crawl log entries."""
    db = SessionLocal()
    try:
        rows = db.query(CrawlLogModel).order_by(
            CrawlLogModel.crawled_at.desc()
        ).limit(limit).all()
        return {"items": [
            {
                "url":        r.url,
                "source":     r.source,
                "title":      r.title,
                "success":    r.success,
                "error":      r.error_msg,
                "crawled_at": r.crawled_at.isoformat() if r.crawled_at else None,
            }
            for r in rows
        ]}
    finally:
        db.close()
