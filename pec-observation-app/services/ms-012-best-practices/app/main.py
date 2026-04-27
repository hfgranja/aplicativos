from fastapi import FastAPI
from pec_shared.telemetry import init_telemetry
from pec_shared.models_base import Base
from .config import settings
from .database import engine
from .adapters.api.practices_router import router as practices_router
from .adapters.events.feedback_consumer import start_consumer, stop_consumer
import redis as redis_lib

init_telemetry(settings.SERVICE_NAME, enabled=settings.OTEL_EXPORTER_ENABLED)

app = FastAPI(title="MS-012 Best Practices", version="1.0.0")
app.include_router(practices_router)

_redis: redis_lib.Redis | None = None


@app.on_event("startup")
def startup():
    global _redis
    Base.metadata.create_all(bind=engine)
    try:
        _redis = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
        start_consumer(_redis)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Redis unavailable, consumer not started: %s", exc)


@app.on_event("shutdown")
def shutdown():
    stop_consumer()


@app.get("/health")
def health():
    return {"status": "healthy", "service": settings.SERVICE_NAME}
