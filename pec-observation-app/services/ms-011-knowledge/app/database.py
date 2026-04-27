from pec_shared.models_base import make_session_factory, get_db_dependency
from app.config import settings

SessionLocal = make_session_factory(settings.DATABASE_URL)
get_db = get_db_dependency(SessionLocal)
