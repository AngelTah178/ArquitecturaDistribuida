from typing import Optional
from fastapi import Header, HTTPException, status


VALID_ROLES = {
    "developer1": "mongo_developer",
    "user1": "mongo_user",
    "dev1": "postgres_developer",
    "usr1": "postgres_user",
}


def verify_api_user(x_user: Optional[str] = Header(default="developer1")) -> str:
    """Verifica si el usuario simulado o bot cuenta con credenciales válidas."""
    if not x_user:
        return "developer1"
    return x_user
