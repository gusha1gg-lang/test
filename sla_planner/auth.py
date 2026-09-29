"""
auth.py — Модуль авторизации.
Сейчас используется MockAuthProvider (заглушка).
При переносе в прод — заменить на ADFSAuthProvider.

Интерфейс провайдера позволяет легко переключаться между
mock-режимом и реальной корпоративной авторизацией.
"""
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from fastapi import Request
from config import settings


@dataclass
class User:
    """Модель пользователя (из JWT claims или mock)."""
    username: str
    full_name: str
    email: str


class AuthProvider(ABC):
    """Абстрактный провайдер авторизации."""

    @abstractmethod
    def get_current_user(self, request: Request) -> User:
        """Получение текущего пользователя из запроса."""
        pass


class MockAuthProvider(AuthProvider):
    """Заглушка для тестов — всегда возвращает Admin."""

    def get_current_user(self, request: Request) -> User:
        return User(
            username="Admin",
            full_name="Администратор",
            email="admin@corp.local",
        )


class ADFSAuthProvider(AuthProvider):
    """
    Провайдер авторизации через ADFS/OAuth2.
    Реализуется при переносе в корпоративную среду.

    При миграции на прод:
    1. Redirect на ADFS_AUTH_URL для получения authorization code
    2. Обмен code на access_token через ADFS_TOKEN_URL
    3. Валидация JWT токена (python-jose)
    4. Извлечение username, email, groups из claims
    5. Проверка членства в нужной AD группе
    """

    def get_current_user(self, request: Request) -> User:
        # Получаем токен из заголовка Authorization
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise Exception("No valid token provided")

        token = auth_header[7:]

        # TODO: Реализовать при переносе в прод
        # from jose import jwt
        #
        # # Получение публичного ключа для валидации
        # # (из ADFS metadata endpoint)
        # key = get_adfs_public_key()
        #
        # # Декодирование и валидация JWT
        # claims = jwt.decode(
        #     token,
        #     key,
        #     algorithms=["RS256"],
        #     audience=settings.ADFS_CLIENT_ID,
        #     issuer=settings.ADFS_AUTH_URL,
        # )
        #
        # # Извлечение данных пользователя
        # return User(
        #     username=claims["preferred_username"],
        #     full_name=claims["name"],
        #     email=claims["email"],
        # )
        #
        # # Проверка групп (опционально)
        # # user_groups = claims.get("groups", [])
        # # if "sla-planner-users" not in user_groups:
        # #     raise Exception("User not authorized")

        raise NotImplementedError(
            "ADFS auth not yet implemented. "
            "Set AUTH_MODE=mock in .env for testing."
        )


def get_auth_provider() -> AuthProvider:
    """Фабрика провайдеров авторизации. Выбор по AUTH_MODE."""
    if settings.AUTH_MODE == "adfs":
        return ADFSAuthProvider()
    return MockAuthProvider()


def get_current_user(request: Request) -> User:
    """FastAPI dependency — возвращает текущего пользователя."""
    provider = get_auth_provider()
    return provider.get_current_user(request)
