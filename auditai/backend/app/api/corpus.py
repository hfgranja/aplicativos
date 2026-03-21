from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.corpus import Corpus, CorpusCase
from app.models.user import User
from app.core.deps import get_current_user
from app.schemas.corpus import CorpusCreate, CorpusCaseCreate, CorpusOut, CorpusCaseOut

router = APIRouter(prefix="/corpus", tags=["corpus"])


@router.post("/{app_id}", response_model=CorpusOut)
def create_corpus(app_id: str, body: CorpusCreate, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    corpus = Corpus(application_id=app_id, **body.model_dump())
    db.add(corpus)
    db.commit()
    db.refresh(corpus)
    return corpus


@router.get("/{app_id}", response_model=List[CorpusOut])
def list_corpora(app_id: str, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    return db.query(Corpus).filter(Corpus.application_id == app_id).all()


@router.post("/{corpus_id}/cases", response_model=CorpusCaseOut)
def add_case(corpus_id: str, body: CorpusCaseCreate, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    corpus = db.query(Corpus).filter(Corpus.id == corpus_id).first()
    if not corpus:
        raise HTTPException(status_code=404, detail="Corpus not found")
    case = CorpusCase(corpus_id=corpus_id, **body.model_dump())
    db.add(case)
    corpus.total_cases += 1
    db.commit()
    db.refresh(case)
    return case


@router.get("/{corpus_id}/cases", response_model=List[CorpusCaseOut])
def list_cases(corpus_id: str, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    return db.query(CorpusCase).filter(CorpusCase.corpus_id == corpus_id).all()
