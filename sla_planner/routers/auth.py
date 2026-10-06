"""
routers/auth.py — Эндпоинты аутентификации.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from auth import (
    authenticate_user, create_token_pair, verify_token, 
    revoke_token, get_current_user, CurrentUser
)
from audit import log_action

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/auth/login", response_model=TokenResponse)
def login(
    login_ LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Аутентификация пользователя и получение токенов.
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        # Логируем неудачную попытку (НЕ логируем пароль!)
        log_action(
            db=db,
            username=login_data.username,
            action="login_failed",
            resource_type="auth",
            resource_name="login",
            details={"reason": "Invalid credentials"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаём токены
    tokens = create_token_pair(user.username)
    
    # Логируем успешный вход
    log_action(
        db=db,
        username=user.username,
        action="login",
        resource_type="auth",
        resource_name="login",
        details={"ip": request.client.host if request.client else None},
        request=request,
    )
    
    logger.info(f"User '{user.username}' logged in successfully")
    return tokens


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_ RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Обновление access токена по refresh токену.
    """
    # Проверяем refresh токен
    try:
        username = verify_token(refresh_data.refresh_token, "refresh")
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверяем что пользователь существует и активен
    from models import User
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Отзываем старый refresh токен
    revoke_token(refresh_data.refresh_token)
    
    # Создаём новую пару токенов
    tokens = create_token_pair(username)
    
    logger.info(f"Token refreshed for user '{username}'")
    return tokens


@router.post("/auth/logout")
def logout(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Выход из системы (отзыв токена).
    """
    # Получаем токен из заголовка
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        revoke_token(token)
    
    # Логируем выход
    log_action(
        db=db,
        username=current_user.username,
        action="logout",
        resource_type="auth",
        resource_name="logout",
        request=request,
    )
    
    logger.info(f"User '{current_user.username}' logged out")
    return {"message": "Successfully logged out"}
