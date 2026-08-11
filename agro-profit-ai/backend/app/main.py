import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import SessionLocal, create_tables
from app.routers import alerts, auth, data_import, farms, fields, scenarios
from app.seed import seed_if_empty

app = FastAPI(
    title="Agro Profit AI",
    description=(
        "Motor de decisão econômica geoespacial para agricultura: integra solo, clima, satélite e dados "
        "do produtor para prever produtividade, risco e margem por hectare, e recomendar a intervenção de "
        "maior valor econômico esperado."
    ),
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

app.include_router(auth.router)
app.include_router(farms.router)
app.include_router(fields.router)
app.include_router(scenarios.router)
app.include_router(alerts.router)
app.include_router(data_import.router)


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
