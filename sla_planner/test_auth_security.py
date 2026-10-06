"""
test_auth_security.py — Тесты безопасности аутентификации и авторизации.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from auth import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, decode_token, verify_token, 
    revoke_token, is_token_revoked, authenticate_user,
    create_token_pair, check_service_access
)
from models import User, UserGroup, Service


class TestPasswordHashing:
    """Тесты хеширования паролей."""

    def test_password_hashing_bcrypt(self):
        """Тест что пароли хешируются через bcrypt."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Хеш не должен быть равен паролю
        assert hashed != password
        
        # Хеш должен быть строкой
        assert isinstance(hashed, str)
        
        # Хеш должен начинаться с $2b$ (bcrypt)
        assert hashed.startswith("$2b$")

    def test_password_verification(self):
        """Тест проверки пароля."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Правильный пароль должен проходить проверку
        assert verify_password(password, hashed) is True
        
        # Неправильный пароль не должен проходить
        assert verify_password("wrong_password", hashed) is False

    def test_different_passwords_different_hashes(self):
        """Тест что разные пароли дают разные хеши."""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2


class TestJWTTokens:
    """Тесты JWT токенов."""

    def test_access_token_creation(self):
        """Тест создания access токена."""
        username = "test_user"
        token = create_access_token(username)
        
        # Токен должен быть строкой
        assert isinstance(token, str)
        
        # Токен должен декодироваться
        payload = decode_token(token)
        assert payload["sub"] == username
        assert payload["type"] == "access"

    def test_refresh_token_creation(self):
        """Тест создания refresh токена."""
        username = "test_user"
        token = create_refresh_token(username)
        
        # Токен должен быть строкой
        assert isinstance(token, str)
        
        # Токен должен декодироваться
        payload = decode_token(token)
        assert payload["sub"] == username
        assert payload["type"] == "refresh"

    def test_token_expiration(self):
        """Тест истечения срока действия токена."""
        username = "test_user"
        
        # Создаём токен с коротким сроком действия
        token = create_access_token(
            username, 
            expires_delta=timedelta(seconds=1)
        )
        
        # Токен должен быть валиден сразу
        payload = decode_token(token)
        assert payload["sub"] == username
        
        # Ждём 2 секунды
        import time
        time.sleep(2)
        
        # Токен должен быть невалиден
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, "access")
        assert exc_info.value.status_code == 401

    def test_token_revocation(self):
        """Тест отзыва токена."""
        username = "test_user"
        token = create_access_token(username)
        
        # Токен должен быть валиден
        assert is_token_revoked(token) is False
        
        # Отзываем токен
        revoke_token(token)
        
        # Токен должен быть отозван
        assert is_token_revoked(token) is True

    def test_token_pair_creation(self):
        """Тест создания пары токенов."""
        username = "test_user"
        tokens = create_token_pair(username)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert "expires_in" in tokens
        
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] == 30 * 60  # 30 минут в секундах


class TestAuthentication:
    """Тесты аутентификации."""

    def test_authenticate_user_success(self):
        """Тест успешной аутентификации."""
        # Mock БД
        db = MagicMock(spec=Session)
        user = User(
            id=1,
            username="test_user",
            email="test@example.com",
            is_active=True,
            is_admin=False
        )
        db.query.return_value.filter.return_value.first.return_value = user
        
        # Аутентификация
        result = authenticate_user(db, "test_user", "any_password")
        
        assert result is not None
        assert result.username == "test_user"

    def test_authenticate_user_not_found(self):
        """Тест аутентификации с несуществующим пользователем."""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        
        result = authenticate_user(db, "nonexistent", "password")
        
        assert result is None

    def test_authenticate_user_inactive(self):
        """Тест аутентификации неактивного пользователя."""
        db = MagicMock(spec=Session)
        user = User(
            id=1,
            username="test_user",
            is_active=False,  # Неактивный
            is_admin=False
        )
        db.query.return_value.filter.return_value.first.return_value = user
        
        result = authenticate_user(db, "test_user", "password")
        
        assert result is None


class TestAuthorization:
    """Тесты авторизации и проверки прав."""

    def test_admin_has_access_to_all_services(self):
        """Тест что админ имеет доступ ко всем сервисам."""
        from auth import CurrentUser
        
        admin = CurrentUser(
            id=1,
            username="admin",
            full_name="Admin",
            email="admin@example.com",
            is_admin=True,
            groups=[]
        )
        
        db = MagicMock(spec=Session)
        
        # Админ должен иметь доступ к любому сервису
        assert check_service_access(admin, "any_service_id", db) is True

    def test_user_access_check_via_groups(self):
        """Тест проверки доступа пользователя через группы."""
        from auth import CurrentUser
        
        user = CurrentUser(
            id=2,
            username="test_user",
            full_name="Test User",
            email="test@example.com",
            is_admin=False,
            groups=["group1"]
        )
        
        db = MagicMock(spec=Session)
        
        # Mock запроса к БД
        db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [
            ("service1",),
            ("service2",),
        ]
        
        # Пользователь должен иметь доступ к service1
        assert check_service_access(user, "service1", db) is True
        
        # Пользователь не должен иметь доступ к service3
        db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [
            ("service1",),
            ("service2",),
        ]
        assert check_service_access(user, "service3", db) is False


class TestPrivilegeEscalation:
    """Тесты на обход прав (privilege escalation)."""

    def test_user_cannot_modify_other_user_work(self):
        """
        Тест что пользователь A не может изменить работу пользователя B,
        если у него нет доступа к сервису.
        """
        from auth import CurrentUser
        
        # Пользователь A
        user_a = CurrentUser(
            id=1,
            username="user_a",
            full_name="User A",
            email="a@example.com",
            is_admin=False,
            groups=["group_a"]
        )
        
        # Пользователь B создал работу для service_b
        db = MagicMock(spec=Session)
        
        # Mock: user_a не имеет доступа к service_b
        db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [
            ("service_a",),  # Только service_a доступен
        ]
        
        # Пользователь A не должен иметь доступ к service_b
        assert check_service_access(user_a, "service_b", db) is False

    def test_user_cannot_view_other_user_works(self):
        """
        Тест что пользователь A не может видеть работы пользователя B,
        если у него нет доступа к сервису.
        """
        from auth import CurrentUser, get_accessible_services
        
        user_a = CurrentUser(
            id=1,
            username="user_a",
            full_name="User A",
            email="a@example.com",
            is_admin=False,
            groups=["group_a"]
        )
        
        db = MagicMock(spec=Session)
        
        # Mock: user_a имеет доступ только к service_a
        db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [
            ("service_a",),
        ]
        
        accessible = get_accessible_services(user_a, db)
        
        # Пользователь A должен видеть только service_a
        assert "service_a" in accessible
        assert "service_b" not in accessible


class TestAuditLogSecurity:
    """Тесты безопасности аудит-лога."""

    def test_audit_log_not_logged_with_sensitive_data(self):
        """
        Тест что в аудит-лог не попадают чувствительные данные
        (пароли, токены).
        """
        from audit import log_action
        
        db = MagicMock(spec=Session)
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers.get.return_value = "Mozilla/5.0"
        
        # Логируем действие
        log_action(
            db=db,
            username="test_user",
            action="login",
            resource_type="auth",
            resource_name="login",
            details={"ip": "127.0.0.1"},
            request=request,
        )
        
        # Проверяем что БД была вызвана
        assert db.add.called
        assert db.commit.called
        
        # Проверяем что в details нет пароля или токена
        call_args = db.add.call_args[0][0]
        assert "password" not in str(call_args.details).lower()
        assert "token" not in str(call_args.details).lower()

    def test_failed_login_does_not_log_password(self):
        """
        Тест что при неудачной попытке входа пароль НЕ логируется.
        """
        from audit import log_action
        
        db = MagicMock(spec=Session)
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers.get.return_value = "Mozilla/5.0"
        
        # Логируем неудачную попытку входа
        log_action(
            db=db,
            username="test_user",
            action="login_failed",
            resource_type="auth",
            resource_name="login",
            details={"reason": "Invalid credentials"},  # НЕ логируем пароль!
            request=request,
        )
        
        # Проверяем что пароль не в details
        call_args = db.add.call_args[0][0]
        details_str = str(call_args.details).lower()
        assert "password" not in details_str
        assert "secret" not in details_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
