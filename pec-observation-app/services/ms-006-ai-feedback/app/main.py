from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pec_shared.telemetry import init_telemetry

init_telemetry()

from .database import create_tables
from .adapters.events.redis_consumer import start_consumer
from .config import settings

app = FastAPI(title="PEC AI Feedback Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
