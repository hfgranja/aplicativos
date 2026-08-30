from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pec_shared.telemetry import init_telemetry

init_telemetry()

from .database import create_tables
from .adapters.api.audio_router import router as audio_router

app = FastAPI(title="PEC Audio Ingestion Service", version="1.0.0")

import os
_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or [],
    allow_credentials=bool(_cors_origins),
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

app.include_router(audio_router)


@app.on_event("startup")
def startup():
    create_tables()


@app.get("/")
def root():
    return {"service": "pec-audio-ingestion", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
