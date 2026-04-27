"""Orchestrate model rebuild — called by scheduler or on demand."""
import logging

from sqlalchemy.orm import Session

from app.adapters.modelfile.builder import rebuild_model as _rebuild
from app.adapters.vector_store.pgvector_store import count_by_type
from app.config import settings
from app.models.embedding import ModelBuild

logger = logging.getLogger(__name__)


def maybe_rebuild(db: Session, force: bool = False) -> ModelBuild | None:
    """Rebuild pec-pedagogo model if enough new examples have accumulated.

    Returns the ModelBuild record if a rebuild was triggered, else None.
    """
    total = count_by_type(db, "approved_feedback")
    last_build = (
        db.query(ModelBuild)
        .filter_by(status="success")
        .order_by(ModelBuild.built_at.desc())
        .first()
    )
    last_count = int(last_build.examples_count) if last_build else 0

    new_since_last = total - last_count
    if not force and new_since_last < settings.rebuild_threshold:
        logger.debug(
            "Skipping rebuild: %d new examples (threshold=%d)",
            new_since_last, settings.rebuild_threshold,
        )
        return None

    logger.info(
        "Triggering model rebuild: %d total examples (%d new)",
        total, new_since_last,
    )
    return _rebuild(
        db=db,
        base_url=settings.ollama_base_url,
        base_model=settings.ollama_model,
        pec_model_name=settings.pec_model_name,
        max_examples=settings.modelfile_max_examples,
    )
