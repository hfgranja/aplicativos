from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pec_shared.telemetry import init_telemetry

init_telemetry()

from .database import create_tables
from .adapters.api.observations_router import router as observations_router

app = FastAPI(title="PEC Observation Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(observations_router)


@app.on_event("startup")
def startup():
    create_tables()


@app.get("/")
def root():
    return {"service": "pec-observation", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
