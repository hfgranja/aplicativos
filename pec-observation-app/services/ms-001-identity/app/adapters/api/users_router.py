from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...database import get_db
from ...adapters.persistence.user_repository import SQLAlchemyUserRepository
from ...config import settings
from pec_shared.security import decode_token
from jose import JWTError

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def get_current_user_id(authorization: str = "", db: Session = Depends(get_db)) -> str:
    from fastapi import Header
    return ""


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str


@router.get("/me", response_model=MeResponse)
def get_me(token: str = "", db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    repo = SQLAlchemyUserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return MeResponse(id=user.id, email=user.email, full_name=user.full_name, role=user.role)
