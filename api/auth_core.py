"""JWT 与演示用户（内存）；生产迁移至 User 表 + 持久化哈希。"""
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from api.config import Settings, get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

Role = str  # "admin" | "annotator" | "viewer"

_users_cache: dict[str, dict[str, Any]] | None = None
_settings_fingerprint: tuple[str, str, str] | None = None


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _users_for_settings(settings: Settings) -> dict[str, dict[str, Any]]:
    """每个进程内按口令缓存一次 bcrypt，避免每次请求重算。"""
    global _users_cache, _settings_fingerprint
    fp = (
        settings.dev_admin_password,
        settings.dev_annotator_password,
        settings.dev_viewer_password,
    )
    if _users_cache is None or _settings_fingerprint != fp:
        _settings_fingerprint = fp
        _users_cache = {
            "admin": {
                "username": "admin",
                "full_name": "系统管理员",
                "role": "admin",
                "password_hash": _hash_password(settings.dev_admin_password),
            },
            "annotator": {
                "username": "annotator",
                "full_name": "标注员",
                "role": "annotator",
                "password_hash": _hash_password(settings.dev_annotator_password),
            },
            "viewer": {
                "username": "viewer",
                "full_name": "只读访客",
                "role": "viewer",
                "password_hash": _hash_password(settings.dev_viewer_password),
            },
        }
    return _users_cache


def authenticate_user(username: str, password: str, settings: Settings) -> dict | None:
    users = _users_for_settings(settings)
    user = users.get(username)
    if not user:
        return None
    if not _verify_password(password, user["password_hash"]):
        return None
    return user


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
    users = _users_for_settings(settings)
    row = users.get(username)
    if not row:
        return None
    return {
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
    }


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
