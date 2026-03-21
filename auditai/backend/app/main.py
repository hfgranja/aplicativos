from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import create_tables, SessionLocal
from app.api import auth, users, tenants, applications, executions, findings, policies, releases, reports, audit, corpus

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AuditAI Test Platform — Enterprise automated software testing with neural intelligence",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tenants.router)
app.include_router(applications.router)
app.include_router(executions.router)
app.include_router(findings.router)
app.include_router(policies.router)
app.include_router(releases.router)
app.include_router(reports.router)
app.include_router(audit.router)
app.include_router(corpus.router)


@app.on_event("startup")
def startup():
    create_tables()
    _seed_admin()


def _seed_admin():
    """Create default admin tenant and user on first startup."""
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.core.security import hash_password

    db = SessionLocal()
    try:
        if db.query(Tenant).first():
            return  # already seeded

        tenant = Tenant(name="AuditAI Platform", slug="auditai")
        db.add(tenant)
        db.flush()

        admin = User(
            tenant_id=tenant.id,
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            full_name="Platform Admin",
            is_admin=True,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
