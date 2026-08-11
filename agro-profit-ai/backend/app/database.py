import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Dev/default: SQLite (zero-dependency). Production: point DATABASE_URL at
# PostgreSQL + PostGIS, e.g. postgresql+psycopg2://user:pass@host/agroprofit
# Geometry columns degrade to plain JSON (GeoJSON) on SQLite and use PostGIS
# geometry types on Postgres — see app/models.py GEOM_TYPE.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/agroprofit.db")
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from app import models  # noqa: F401 ensure models are registered

    if IS_POSTGRES:
        with engine.connect() as conn:
            conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS postgis")
            conn.commit()
    Base.metadata.create_all(bind=engine)
