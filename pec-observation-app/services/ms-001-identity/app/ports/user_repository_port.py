from abc import ABC, abstractmethod
from typing import Optional
from ..domain.user import UserDomain


class UserRepositoryPort(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[UserDomain]:
        ...

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[UserDomain]:
        ...

    @abstractmethod
    def create(self, email: str, hashed_password: str, full_name: str, role: str) -> UserDomain:
        ...
