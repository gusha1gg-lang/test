"""
routers/users.py — Управление пользователями и группами.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, CurrentUser, check_service_access
from models import (
    User, UserGroup, Service,
    UserCreate, UserUpdate, UserResponse,
    GroupCreate, GroupUpdate, GroupResponse, ServiceResponse,
    UserAccessCheck,
    user_group_association, group_service_association
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


# ============================================
# Пользователи
# ============================================

@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Получение списка всех пользователей."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут просматривать список пользователей")
    
    users = db.query(User).order_by(User.username).all()
    return users


@router.get("/users/me", response_model=UserResponse)
def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Получение информации о текущем пользователе."""
    user = db.query(User).filter(User.username == current_user.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Создание нового пользователя (только для администраторов)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут создавать пользователей")
    
    # Проверка уникальности username
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким username уже существует")
    
    # Проверка уникальности email
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    # Создание пользователя
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        is_admin=user_data.is_admin,
    )
    
    # Добавление в группы
    if user_data.group_ids:
        groups = db.query(UserGroup).filter(UserGroup.id.in_(user_data.group_ids)).all()
        new_user.groups = groups
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"User '{new_user.username}' created by '{current_user.username}'")
    return new_user


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Обновление пользователя (только для администраторов)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут изменять пользователей")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Обновление полей
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.is_admin is not None:
        user.is_admin = user_data.is_admin
    
    # Обновление групп
    if user_data.group_ids is not None:
        groups = db.query(UserGroup).filter(UserGroup.id.in_(user_data.group_ids)).all()
        user.groups = groups
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User '{user.username}' updated by '{current_user.username}'")
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Удаление пользователя (только для администраторов)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут удалять пользователей")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Нельзя удалить самого себя
    if user.username == current_user.username:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")
    
    username = user.username
    db.delete(user)
    db.commit()
    
    logger.info(f"User '{username}' deleted by '{current_user.username}'")


# ============================================
# Группы
# ============================================

@router.get("/groups", response_model=List[GroupResponse])
def list_groups(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Получение списка всех групп."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут просматривать список групп")
    
    groups = db.query(UserGroup).order_by(UserGroup.name).all()
    
    # Добавляем количество пользователей и сервисов
    result = []
    for group in groups:
        group_data = GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            created_at=group.created_at,
            users_count=len(group.users),
            services_count=len(group.services),
            services=[
                ServiceResponse(
                    id=s.id,
                    name=s.name,
                    status=s.status,
                    algorithm=s.algorithm,
                    parent_id=s.parent_id,
                ) for s in group.services
            ]
        )
        result.append(group_data)
    
    return result


@router.post("/groups", response_model=GroupResponse, status_code=201)
def create_group(
    group_data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Создание новой группы (только для администраторов)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут создавать группы")
    
    # Проверка уникальности имени
    existing = db.query(UserGroup).filter(UserGroup.name == group_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Группа с таким именем уже существует")
    
    # Создание группы
    new_group = UserGroup(
        name=group_data.name,
        description=group_data.description,
    )
    
    # Добавление сервисов
    if group_data.service_ids:
        services = db.query(Service).filter(Service.id.in_(group_data.service_ids)).all()
        new_group.services = services
    
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    
    logger.info(f"Group '{new_group.name}' created by '{current_user.username}'")
    
    return GroupResponse(
        id=new_group.id,
        name=new_group.name,
        description=new_group.description,
        created_at=new_group.created_at,
        users_count=0,
        services_count=len(new_group.services),
        services=[
            ServiceResponse(
                id=s.id,
                name=s.name,
                status=s.status,
                algorithm=s.algorithm,
                parent_id=s.parent_id,
            ) for s in new_group.services
        ]
    )


@router.patch("/groups/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: int,
    group_data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Обновление группы (только для администраторов)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут изменять группы")
    
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    # Обновление полей
    if group_data.name is not None:
        group.name = group_data.name
    if group_data.description is not None:
        group.description = group_data.description
    
    # Обновление сервисов
    if group_data.service_ids is not None:
        services = db.query(Service).filter(Service.id.in_(group_data.service_ids)).all()
        group.services = services
    
    db.commit()
    db.refresh(group)
    
    logger.info(f"Group '{group.name}' updated by '{current_user.username}'")
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        users_count=len(group.users),
        services_count=len(group.services),
        services=[
            ServiceResponse(
                id=s.id,
                name=s.name,
                status=s.status,
                algorithm=s.algorithm,
                parent_id=s.parent_id,
            ) for s in group.services
        ]
    )


@router.delete("/groups/{group_id}", status_code=204)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Удаление группы (только для администраторов)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администраторы могут удалять группы")
    
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    group_name = group.name
    db.delete(group)
    db.commit()
    
    logger.info(f"Group '{group_name}' deleted by '{current_user.username}'")


# ============================================
# Проверка доступа
# ============================================

@router.get("/access/check", response_model=UserAccessCheck)
def check_access(
    service_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Проверка доступа текущего пользователя к сервису."""
    has_access = check_service_access(current_user, service_id, db)
    
    reason = "Доступ разрешён"
    if not has_access:
        if current_user.is_admin:
            reason = "Администратор имеет доступ ко всем сервисам"
        else:
            reason = "У пользователя нет доступа к этому сервису. Обратитесь к администратору."
    
    return UserAccessCheck(
        username=current_user.username,
        service_id=service_id,
        has_access=has_access,
        reason=reason,
    )


@router.get("/access/services", response_model=List[ServiceResponse])
def get_accessible_services(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Получение списка сервисов, доступных текущему пользователю."""
    from auth import get_accessible_services as get_services
    
    service_ids = get_services(current_user, db)
    
    if not service_ids:
        return []
    
    services = db.query(Service).filter(Service.id.in_(service_ids)).all()
    
    return [
        ServiceResponse(
            id=s.id,
            name=s.name,
            status=s.status,
            algorithm=s.algorithm,
            parent_id=s.parent_id,
        ) for s in services
    ]
