from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_access_token(user)
    return schemas.TokenResponse(
        access_token=token,
        user_id=user.id,
        tenant_id=user.tenant_id,
        full_name=user.full_name,
        role=user.role,
    )
