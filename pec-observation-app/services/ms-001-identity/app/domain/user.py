from dataclasses import dataclass
from typing import Optional


@dataclass
class UserDomain:
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    district_id: Optional[str] = None
