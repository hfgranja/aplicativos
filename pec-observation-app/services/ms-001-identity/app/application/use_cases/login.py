from dataclasses import dataclass
from typing import Optional
from ...ports.user_repository_port import UserRepositoryPort
from pec_shared.security import verify_password, create_access_token, create_refresh_token


@dataclass
class LoginInput:
    email: str
    password: str


@dataclass
class TokenOutput:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str = ""
    role: str = ""


class AuthenticationError(Exception):
    pass


class LoginUseCase:
    def __init__(self, repo, hashed_pw_getter, secret_key: str,
                 access_expire_min: int, refresh_expire_days: int, algorithm: str):
        self._repo = repo
        self._hashed_pw_getter = hashed_pw_getter
        self._secret_key = secret_key
        self._access_expire = access_expire_min
        self._refresh_expire = refresh_expire_days
        self._algorithm = algorithm

    def execute(self, input: LoginInput) -> TokenOutput:
        user = self._repo.get_by_email(input.email)
        if not user:
            raise AuthenticationError("Invalid credentials")

        hashed = self._hashed_pw_getter(input.email)
        if not verify_password(input.password, hashed):
            raise AuthenticationError("Invalid credentials")

        if not user.is_active:
            raise AuthenticationError("Account disabled")

        access = create_access_token(
            subject=user.id,
            secret_key=self._secret_key,
            algorithm=self._algorithm,
            expire_minutes=self._access_expire,
            extra_claims={"role": user.role, "email": user.email},
        )
        refresh = create_refresh_token(
            subject=user.id,
            secret_key=self._secret_key,
            algorithm=self._algorithm,
            expire_days=self._refresh_expire,
        )
        return TokenOutput(access_token=access, refresh_token=refresh,
                           user_id=user.id, role=user.role)
