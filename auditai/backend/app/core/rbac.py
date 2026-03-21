from functools import wraps
from fastapi import HTTPException
from app.models.user import User

PERMISSIONS = {
    "admin": ["*"],
    "engineer": [
        "application:read", "application:write",
        "execution:read", "execution:write",
        "finding:read", "finding:write",
        "corpus:read", "corpus:write",
        "contract:read", "contract:write",
        "report:read",
    ],
    "viewer": [
        "application:read", "execution:read",
        "finding:read", "report:read",
    ],
    "security": [
        "application:read", "execution:read", "execution:write",
        "finding:read", "finding:write", "finding:accept_risk",
        "policy:read", "policy:write", "report:read",
    ],
    "auditor": [
        "application:read", "execution:read",
        "finding:read", "audit:read", "report:read", "release:read",
    ],
}


def user_has_permission(user: User, permission: str) -> bool:
    if user.is_admin:
        return True
    for role in user.roles:
        role_perms = PERMISSIONS.get(role.name, [])
        if "*" in role_perms or permission in role_perms:
            return True
    return False


def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = None, **kwargs):
            if current_user and not user_has_permission(current_user, permission):
                raise HTTPException(status_code=403, detail=f"Permission '{permission}' required")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
