"""Unit tests for the Identity service auth use case."""
import pytest
from app.application.use_cases.login import LoginInput, LoginUseCase, AuthenticationError
from app.domain.user import UserDomain


class MockUserRepo:
    def __init__(self, user=None, hashed=""):
        self._user = user
        self._hashed = hashed

    def get_by_email(self, email):
        return self._user

    def get_by_id(self, user_id):
        return self._user

    def create(self, email, hashed_password, full_name, role):
        return self._user


def _make_use_case(repo, hashed_pw="hashed"):
    return LoginUseCase(
        repo=repo,
        hashed_pw_getter=lambda email: hashed_pw,
        secret_key="test-secret-key-long-enough-for-hs256",
        access_expire_min=60,
        refresh_expire_days=7,
        algorithm="HS256",
    )


def test_login_unknown_user_raises():
    repo = MockUserRepo(user=None)
    use_case = _make_use_case(repo)
    with pytest.raises(AuthenticationError):
        use_case.execute(LoginInput(email="unknown@test.com", password="pass"))


def test_login_inactive_user_raises():
    user = UserDomain(id="1", email="a@b.com", full_name="A", role="pec", is_active=False)
    repo = MockUserRepo(user=user)
    from pec_shared.security import hash_password
    hashed = hash_password("correct")
    use_case = LoginUseCase(
        repo=repo,
        hashed_pw_getter=lambda e: hashed,
        secret_key="test-secret-key-long-enough-for-hs256",
        access_expire_min=60,
        refresh_expire_days=7,
        algorithm="HS256",
    )
    with pytest.raises(AuthenticationError, match="disabled"):
        use_case.execute(LoginInput(email="a@b.com", password="correct"))


def test_login_wrong_password_raises():
    user = UserDomain(id="1", email="a@b.com", full_name="A", role="pec", is_active=True)
    from pec_shared.security import hash_password
    hashed = hash_password("correct_password")
    repo = MockUserRepo(user=user)
    use_case = LoginUseCase(
        repo=repo,
        hashed_pw_getter=lambda e: hashed,
        secret_key="test-secret-key-long-enough-for-hs256",
        access_expire_min=60,
        refresh_expire_days=7,
        algorithm="HS256",
    )
    with pytest.raises(AuthenticationError):
        use_case.execute(LoginInput(email="a@b.com", password="wrong_password"))
