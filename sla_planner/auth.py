"""
auth.py — Модуль авторизации.
Поддерживает mock-режим и работу с реальными пользователями из БД.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass
from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import User, UserGroup, user_group_association


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
    """

    def get_current_user(self, request: Request, db: Session) -> CurrentUser:
        # Ищем администратора в БД
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
