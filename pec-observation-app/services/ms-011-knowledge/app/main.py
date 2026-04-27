from fastapi import FastAPI
from pec_shared.telemetry import init_telemetry
from app.config import settings
from app.database import SessionLocal
from app.models.document import KnowledgeDocumentModel, DocumentChunkModel
from app.models.feedback_style import FeedbackStyleModel
from app.adapters.api.knowledge_router import router as knowledge_router
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


@app.get("/health")
def health():
    return {"status": "healthy", "service": settings.SERVICE_NAME}
