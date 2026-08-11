"""Autenticação JWT + RBAC (spec seções 48-49).

Multi-tenancy: toda query de domínio é filtrada por tenant_id extraído do
token — nenhuma rota de dados aceita tenant_id vindo do cliente.
"""
import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user: models.User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "role": user.role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


class CurrentUser:
    def __init__(self, user_id: str, tenant_id: str, role: str):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        role = payload.get("role", "Viewer")
        if not user_id or not tenant_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        return CurrentUser(user_id=user_id, tenant_id=tenant_id, role=role)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível validar credenciais",
        )


def require_farm_in_tenant(farm: models.Farm, current_user: CurrentUser) -> None:
    if farm.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Recurso não pertence ao tenant autenticado")
