import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    CommentRepoDep,
    CommentServiceDep,
    CurrentUserDep,
    get_comment_for_update,
)
from app.models.comment import Comment
from app.schemas.comment import CommentCreateIn, CommentResponse, CommentUpdate

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreateIn,
    service: CommentServiceDep,
    current_user: CurrentUserDep,
):
    """Создать новый комментарий (любой авторизованный пользователь)."""
    return await service.create_comment(comment_data, author=current_user)


@router.get("/", response_model=list[CommentResponse])
async def get_all_comments(
    comment_repo: CommentRepoDep,
    current_user: CurrentUserDep,
    skip: int = 0,
    limit: int = 100,
    news_id: uuid.UUID | None = Query(None, description="Filter comments by news ID"),
):
    """Получить список комментариев."""
    return await comment_repo.get_multi(skip=skip, limit=limit, news_id=news_id)


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(comment_id: uuid.UUID, service: CommentServiceDep, current_user: CurrentUserDep):
    """Получить комментарий по ID."""
    return await service.get_by_id(comment_id)


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment_partial(
    comment_data: CommentUpdate,
    service: CommentServiceDep,
    comment_to_update: Annotated[Comment, Depends(get_comment_for_update)],
):
    """Частично обновить комментарий (автор или админ)."""
    return await service.update_comment(comment_to_update, comment_data)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    service: CommentServiceDep,
    comment_to_delete: Annotated[Comment, Depends(get_comment_for_update)],
):
    """Удалить комментарий (автор или админ)."""
    await service.delete_comment(comment_to_delete)
