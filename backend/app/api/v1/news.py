import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    CurrentUserDep,
    NewsRepoDep,
    NewsServiceDep,
    get_news_for_update,
    require_role,
)
from app.models.news import News
from app.models.user import User
from app.schemas.news import NewsCreateIn, NewsResponse, NewsUpdate
from app.schemas.role import UserRole

router = APIRouter(prefix="/news", tags=["news"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_news(
    news_data: NewsCreateIn,
    service: NewsServiceDep,
    current_user: Annotated[User, Depends(require_role([UserRole.ADMIN, UserRole.VERIFIED_AUTHOR]))],
) -> NewsResponse:
    """Создать новость (только верифицированный автор или админ)."""
    return await service.create_news(news_data, current_user)


@router.get("/")
async def get_all_news(
    news_repo: NewsRepoDep,
    _current_user: CurrentUserDep,
    skip: int = 0,
    limit: int = 100,
) -> list[NewsResponse]:
    """Получить список всех новостей."""
    news_list = await news_repo.get_multi(skip=skip, limit=limit)
    return [NewsResponse.model_validate(news) for news in news_list]


@router.get("/{news_id}")
async def get_news(
    news_id: uuid.UUID,
    service: NewsServiceDep,
    _current_user: CurrentUserDep,
) -> NewsResponse:
    """Получить одну новость по ID."""
    news = await service.get_by_id(news_id)
    # Сервис уже сам выбрасывает 404, но проверка для надежности не помешает
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news


@router.patch("/{news_id}")
async def update_news_partial(
    news_update_data: NewsUpdate,
    service: NewsServiceDep,
    news_to_update: Annotated[News, Depends(get_news_for_update)],
) -> NewsResponse:
    """Частично обновить новость (автор или админ)."""
    return await service.update_news(news_to_update, news_update_data)


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(
    service: NewsServiceDep,
    news_to_delete: Annotated[News, Depends(get_news_for_update)],
) -> None:
    """Удалить новость (автор или админ)."""
    await service.delete_news(news_to_delete)
