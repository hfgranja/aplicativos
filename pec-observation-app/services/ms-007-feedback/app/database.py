from pec_shared.models_base import Base, make_session_factory
from .config import settings

SessionLocal, engine = make_session_factory(settings.DATABASE_URL)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
