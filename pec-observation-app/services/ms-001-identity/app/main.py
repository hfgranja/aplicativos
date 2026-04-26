from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pec_shared.telemetry import init_telemetry

init_telemetry()

from .database import create_tables, SessionLocal
from .adapters.api.auth_router import router as auth_router
from .adapters.api.users_router import router as users_router
from .config import settings

app = FastAPI(title="PEC Identity Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)


@app.on_event("startup")
def startup():
    create_tables()
    _seed_admin()


def _seed_admin():
    from .models.user import User
    from pec_shared.security import hash_password

    db = SessionLocal()
    try:
        if db.query(User).first():
            return
        admin = User(
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            full_name="Administrador PEC",
            role="admin",
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()


@app.get("/")
def root():
    return {"service": "pec-identity", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
