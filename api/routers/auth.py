from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from api.auth_core import authenticate_user, create_access_token, get_current_user
from api.config import Settings, get_settings

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
):
    user = authenticate_user(form_data.username, form_data.password, settings)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    token = create_access_token(
        {"username": user["username"], "role": user["role"]},
        settings,
    )
    return TokenResponse(
        access_token=token,
        role=user["role"],
        username=user["username"],
        full_name=user["full_name"],
    )


@router.get("/me", response_model=UserOut)
def me(current: Annotated[dict, Depends(get_current_user)]):
    return UserOut(**current)
