from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth_core import authenticate_user, create_access_token, get_current_user, user_to_dict
from api.config import Settings, get_settings
from api.deps import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    full_name: str


class UserOut(BaseModel):
    username: str
    full_name: str
    role: str


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    u = user_to_dict(user)
    token = create_access_token({"username": u["username"], "role": u["role"]}, settings)
    return TokenResponse(
        access_token=token,
        role=u["role"],
        username=u["username"],
        full_name=u["full_name"],
    )


@router.get("/me", response_model=UserOut)
def me(current: Annotated[dict, Depends(get_current_user)]):
    return UserOut(
        username=current["username"],
        full_name=current["full_name"],
        role=current["role"],
    )
