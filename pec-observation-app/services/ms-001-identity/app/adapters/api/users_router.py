from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from ...database import get_db
from ...adapters.persistence.user_repository import SQLAlchemyUserRepository
from ...config import settings
from pec_shared.security import decode_token
from jose import JWTError

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def get_current_user_id(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError("no sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_id


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str


@router.get("/me", response_model=MeResponse)
def get_me(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    repo = SQLAlchemyUserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return MeResponse(id=user.id, email=user.email, full_name=user.full_name, role=user.role)
