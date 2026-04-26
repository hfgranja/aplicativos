from typing import Optional
from sqlalchemy.orm import Session
from ...models.user import User
from ...ports.user_repository_port import UserRepositoryPort
from ...domain.user import UserDomain


class SQLAlchemyUserRepository(UserRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def _to_domain(self, user: User) -> UserDomain:
        return UserDomain(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            district_id=user.district_id,
        )

    def get_by_email(self, email: str) -> Optional[UserDomain]:
        user = self._db.query(User).filter(User.email == email).first()
        return self._to_domain(user) if user else None

    def get_by_id(self, user_id: str) -> Optional[UserDomain]:
        user = self._db.query(User).filter(User.id == user_id).first()
        return self._to_domain(user) if user else None

    def create(self, email: str, hashed_password: str, full_name: str, role: str) -> UserDomain:
        user = User(email=email, hashed_password=hashed_password,
                    full_name=full_name, role=role)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return self._to_domain(user)

    def get_raw(self, email: str) -> Optional[User]:
        return self._db.query(User).filter(User.email == email).first()
