from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...database import get_db
from ...adapters.persistence.user_repository import SQLAlchemyUserRepository
from ...application.use_cases.login import LoginInput, LoginUseCase, AuthenticationError
from ...config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: str
    role: str


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    repo = SQLAlchemyUserRepository(db)

    def get_hashed(email: str) -> str:
        raw = repo.get_raw(email)
        return raw.hashed_password if raw else ""

    use_case = LoginUseCase(
        repo=repo,
        hashed_pw_getter=get_hashed,
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        access_expire_min=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
    try:
        result = use_case.execute(LoginInput(email=body.email, password=body.password))
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        user_id=result.user_id,
        role=result.role,
    )
