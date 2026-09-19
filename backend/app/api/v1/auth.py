from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_sso.sso.github import GithubSSO
from pydantic import BaseModel

from app.api.dependencies import (
    AuthServiceDep,
    CurrentUserDep,
    DBSession,
    UserServiceDep,
)
from app.core.config import settings
from app.schemas.refresh_token import RefreshTokenRequest, RefreshTokenResponseFromCache
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105


def get_github_sso() -> GithubSSO:
    """Возвращает экземпляр GithubSSO с настройками из .env."""
    return GithubSSO(
        settings.GITHUB_CLIENT_ID,
        settings.GITHUB_CLIENT_SECRET,
        settings.GITHUB_CALLBACK_URL,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    service: UserServiceDep,
) -> UserResponse:
    """Регистрация нового пользователя."""
    return await service.create_user(user_data)


@router.post("/login")
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
) -> TokenResponse:
    """Получение access и refresh токенов по email и паролю."""
    token_data = await service.login(
        form_data=form_data,
        user_agent=request.headers.get("user-agent"),
    )
    return TokenResponse(**token_data)


@router.get("/github/login")
async def github_login(
    github_sso: Annotated[GithubSSO, Depends(get_github_sso)],
) -> TokenResponse:
    """Генерирует URL для редиректа на GitHub для аутентификации."""
    async with github_sso as sso:
        return await sso.get_login_redirect()


@router.get("/github/callback")
async def github_callback(
    request: Request,
    session: DBSession,
    service: AuthServiceDep,
    github_sso: Annotated[GithubSSO, Depends(get_github_sso)],
) -> TokenResponse:
    """Обрабатывает коллбэк от GitHub после аутентификации."""
    async with github_sso as sso:
        user_info = await sso.verify_and_process(request)

    if not user_info:
        raise HTTPException(status_code=400, detail="GitHub login failed")

    token_data = await service.handle_sso_callback(
        session=session,
        user_info=user_info,
        user_agent=request.headers.get("user-agent"),
    )
    return TokenResponse(**token_data)


@router.post("/refresh")
async def refresh_access_token(
    request_body: RefreshTokenRequest,
    service: AuthServiceDep,
) -> TokenResponse:
    """Обновление access-токена с помощью refresh-токена."""
    token_data = await service.refresh_token(refresh_token=request_body.refresh_token)
    return TokenResponse(**token_data)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request_body: RefreshTokenRequest,
    service: AuthServiceDep,
) -> None:
    """Выход из системы (удаление refresh-токена)."""
    await service.logout(refresh_token=request_body.refresh_token)


@router.get("/sessions/me")
async def get_my_sessions(
    current_user: CurrentUserDep,
    service: AuthServiceDep,
) -> list[RefreshTokenResponseFromCache]:
    """Получение списка активных сессий текущего пользователя из Redis."""
    sessions = await service.get_user_sessions(user_id=str(current_user.id))
    return [RefreshTokenResponseFromCache.model_validate(session) for session in sessions]
