"""JWT 与数据库用户。"""
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import Settings, get_settings
from api.deps import get_db
from db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

Role = str  # "admin" | "annotator" | "viewer"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def user_to_dict(row: User) -> dict:
    return {
        "username": row.username,
        "full_name": row.full_name or "",
        "role": row.role,
        "id": row.id,
    }


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    row = db.scalar(select(User).where(User.username == username, User.is_active.is_(True)))
    if row is None:
        return None
    if not verify_password(password, row.password_hash):
        return None
    return row


def create_access_token(subject: dict, settings: Settings) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject["username"], "role": subject["role"], "exp": expire}
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str, settings: Settings) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


async def get_current_user_optional(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> dict | None:
    if not token:
        return None
    try:
        payload = decode_token(token, settings)
        username: str = payload.get("sub", "")
        if not username:
            return None
    except JWTError:
        return None
    row = db.scalar(select(User).where(User.username == username, User.is_active.is_(True)))
    if row is None:
        return None
    return user_to_dict(row)


async def get_current_user(
    user: Annotated[dict | None, Depends(get_current_user_optional)],
) -> dict:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或令牌无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*allowed: Role):
    async def _dep(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if user["role"] not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return user

    return _dep
