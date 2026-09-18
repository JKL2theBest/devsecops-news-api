import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    CurrentUserDep,
    UserRepoDep,
    UserServiceDep,
    get_user_for_update,
    require_role,
)
from app.models.user import User
from app.schemas.role import UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, service: UserServiceDep):
    """Создать нового пользователя."""
    return await service.create_user(user_data)


@router.get("/", response_model=list[UserResponse])
async def get_all_users(
    user_repo: UserRepoDep,
    _current_user: CurrentUserDep,
    skip: int = 0,
    limit: int = 100,
):
    """Получить список всех пользователей."""
    return await user_repo.get_multi(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, service: UserServiceDep, _current_user: CurrentUserDep):
    """Получить одного пользователя по ID."""
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_partial(
    user_data: UserUpdate,
    service: UserServiceDep,
    user_to_update: Annotated[User, Depends(get_user_for_update)],
):
    """Частично обновить данные пользователя (свои или админом)."""
    return await service.update_user(user_to_update, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    service: UserServiceDep,
    _admin_user: Annotated[User, Depends(require_role([UserRole.ADMIN]))],
) -> None:
    """Удалить пользователя (только админ)."""
    await service.delete_user(user_id)
