import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import SessionLocal, create_tables
from app.routers import audit, intents, merchants, metrics, webhooks
from app.seed import seed_if_empty

app = FastAPI(
    title="Receivables Orchestrator API",
    description="Motor Inteligente de Recebimentos — decide/recomenda o melhor caminho de recebimento "
                "entre Pix, cartão e boleto, com fallback, retry, explicabilidade e auditoria.",
    version="0.1.0",
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(merchants.router)
app.include_router(intents.router)
app.include_router(webhooks.router)
app.include_router(metrics.router)
app.include_router(audit.router)


@app.on_event("startup")
def on_startup():
    create_tables()
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
