from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pec_shared.telemetry import init_telemetry

init_telemetry()

from .database import create_tables
from .adapters.events.redis_consumer import start_consumer
from .config import settings

app = FastAPI(title="PEC AI Feedback Service", version="1.0.0")

import os
_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or [],
    allow_credentials=bool(_cors_origins),
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.on_event("startup")
def startup():
    create_tables()
    start_consumer(settings.REDIS_URL)


@app.get("/")
def root():
    return {"service": "pec-ai-feedback", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
