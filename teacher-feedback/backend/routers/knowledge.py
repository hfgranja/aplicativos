from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import knowledge_service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/index-observation/{obs_id}")
def index_observation(obs_id: str, db: Session = Depends(get_db)):
    count = knowledge_service.index_observation(db, obs_id)
    return {"ok": True, "indexed": count}


@router.get("/best-practices")
def get_best_practices(
    subject: str = "",
    grade_band: str = "",
    limit: int = 5,
    db: Session = Depends(get_db),
):
    practices = knowledge_service.get_best_practices(db, subject, grade_band, limit)
    return {"practices": practices, "total": len(practices)}


@router.get("/similar-context")
def get_similar_context(
    subject: str = "",
    grade: str = "",
    weak_sections: str = "",
    limit: int = 5,
    db: Session = Depends(get_db),
):
    results = knowledge_service.get_similar_context(db, subject, grade, weak_sections, limit)
    return {"results": results, "total": len(results)}
