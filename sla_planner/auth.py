"""
auth.py — Модуль авторизации.
Поддерживает mock-режим и работу с реальными пользователями из БД.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from config import settings
from database import get_db
from models import User, UserGroup, user_group_association

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Секретный ключ для JWT (должен быть в .env)
SECRET_KEY = settings.get("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ============================================
# Хеширование паролей
# ============================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля."""
    return pwd_context.hash(password)


# ============================================
# JWT токены
# ============================================

def create_access_token( username: str, expires_delta: Optional[timedelta] = None) -> str:
    """Создание access токена."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": username,
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token( str) -> str:
    """Создание refresh токена."""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire,
        "sub": username,
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Декодирование JWT токена."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_token(token: str, token_type: str = "access") -> str:
    """Проверка токена и возврат username."""
    payload = decode_token(token)
    username: str = payload.get("sub")
    token_type_from_payload: str = payload.get("type")
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if token_type_from_payload != token_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type. Expected {token_type}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return username


# ============================================
# Отзыв токенов (базовая реализация)
# ============================================

# В продакшене использовать Redis или БД для хранения отозванных токенов
_revoked_tokens: set = set()

def revoke_token(token: str):
    """Отзыв токена."""
    _revoked_tokens.add(token)


def is_token_revoked(token: str) -> bool:
    """Проверка отзыва токена."""
    return token in _revoked_tokens


@dataclass
class CurrentUser:
    """Текущий пользователь (для dependency injection)."""
    id: int
    username: str
    full_name: str
    email: str
    is_admin: bool
    groups: List[str]  # Названия групп


class AuthProvider(ABC):
    """Абстрактный провайдер авторизации."""

    @abstractmethod
    def get_current_user(self, request: Request, db: Session) -> CurrentUser:
        """Получение текущего пользователя из запроса."""
        pass


class MockAuthProvider(AuthProvider):
    """
    Заглушка для тестов.
    Возвращает первого администратора из БД или создаёт дефолтного.
    
    ВНИМАНИЕ: В продакшене использовать ADFSAuthProvider с JWT!
    """

    def get_current_user(self, request: Request, db: Session) -> CurrentUser:
        # Получаем токен из заголовка Authorization (если есть)
        auth_header = request.headers.get("Authorization", "")
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            
            # Проверяем отзыв токена
            if is_token_revoked(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Проверяем и декодируем токен
            try:
                username = verify_token(token, "access")
            except HTTPException:
                # Если токен невалиден, используем mock-режим
                username = None
        else:
            username = None
        
        # Если токен есть и валиден — ищем пользователя в БД
        if username:
            user = db.query(User).filter(User.username == username, User.is_active == True).first()
            if user:
                groups = [g.name for g in user.groups]
                return CurrentUser(
                    id=user.id,
                    username=user.username,
                    full_name=user.full_name or user.username,
                    email=user.email or "",
                    is_admin=user.is_admin,
                    groups=groups,
                )
        
        # Mock-режим: возвращаем первого администратора или дефолтного
        admin = db.query(User).filter(User.is_admin == True, User.is_active == True).first()
        
        if admin:
            groups = [g.name for g in admin.groups]
            return CurrentUser(
                id=admin.id,
                username=admin.username,
                full_name=admin.full_name or admin.username,
                email=admin.email or "",
                is_admin=admin.is_admin,
                groups=groups,
            )
        
        # Если нет пользователей — возвращаем дефолтного
        return CurrentUser(
            id=0,
            username="Admin",
            full_name="Администратор",
            email="admin@corp.local",
            is_admin=True,
            groups=[],
        )


class ADFSAuthProvider(AuthProvider):
    """
    Провайдер авторизации через ADFS/OAuth2.
    Реализуется при переносе в корпоративную среду.
    """

    def get_current_user(self, request: Request, db: Session) -> CurrentUser:
        # Получаем токен из заголовка Authorization
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="No valid token provided")

        token = auth_header[7:]

        # TODO: Реализовать при переносе в прод
        # from jose import jwt
        # claims = jwt.decode(token, key, algorithms=["RS256"])
        # username = claims["preferred_username"]
        
        # Ищем пользователя в БД
        # user = db.query(User).filter(User.username == username).first()
        # if not user:
        #     raise HTTPException(status_code=403, detail="User not found")
        
        # groups = [g.name for g in user.groups]
        # return CurrentUser(
        #     id=user.id,
        #     username=user.username,
        #     full_name=user.full_name or user.username,
        #     email=user.email or "",
        #     is_admin=user.is_admin,
        #     groups=groups,
        # )

        raise NotImplementedError(
            "ADFS auth not yet implemented. "
            "Set AUTH_MODE=mock in .env for testing."
        )


def get_auth_provider() -> AuthProvider:
    """Фабрика провайдеров авторизации."""
    if settings.AUTH_MODE == "adfs":
        return ADFSAuthProvider()
    return MockAuthProvider()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> CurrentUser:
    """FastAPI dependency — возвращает текущего пользователя."""
    provider = get_auth_provider()
    return provider.get_current_user(request, db)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Аутентификация пользователя по username и password."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    # В текущей реализации пароли не хранятся (mock-режим)
    # В продакшене добавить поле password_hash в модель User
    # и проверять: if not verify_password(password, user.password_hash): return None
    if not user.is_active:
        return None
    return user


def create_token_pair( str) -> dict:
    """Создание пары access и refresh токенов."""
    access_token = create_access_token(username)
    refresh_token = create_refresh_token(username)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def check_service_access(
    user: CurrentUser,
    service_id: str,
    db: Session,
) -> bool:
    """
    Проверка доступа пользователя к сервису.
    Администраторы имеют доступ ко всем сервисам.
    Обычные пользователи — только к тем, что доступны через их группы.
    """
    # Администраторы имеют доступ ко всему
    if user.is_admin:
        return True
    
    # Получаем ID сервисов, доступных через группы пользователя
    accessible_service_ids = db.query(
        user_group_association.c.service_id
    ).join(
        UserGroup, user_group_association.c.group_id == UserGroup.id
    ).join(
        User, user_group_association.c.user_id == User.id
    ).filter(
        User.username == user.username,
        User.is_active == True,
    ).all()
    
    # Проверяем, есть ли сервис в списке доступных
    accessible_ids = [row[0] for row in accessible_service_ids]
    return service_id in accessible_ids


def get_accessible_services(
    user: CurrentUser,
    db: Session,
) -> List[str]:
    """
    Получение списка ID сервисов, доступных пользователю.
    """
    from models import Service, group_service_association
    
    # Администраторы видят все сервисы
    if user.is_admin:
        all_services = db.query(Service).all()
        return [s.id for s in all_services]
    
    # Обычные пользователи — только через группы
    accessible = db.query(
        group_service_association.c.service_id
    ).join(
        UserGroup, group_service_association.c.group_id == UserGroup.id
    ).join(
        User, user_group_association.c.group_id == UserGroup.id
    ).filter(
        User.username == user.username,
        User.is_active == True,
    ).all()
    
    return [row[0] for row in accessible]
