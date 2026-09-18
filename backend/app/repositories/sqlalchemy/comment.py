import uuid
from typing import ClassVar

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from app.models.comment import Comment
from app.repositories.sqlalchemy.base import SQLAlchemyRepository
from app.schemas.comment import CommentCreate, CommentUpdate


class CommentRepository(SQLAlchemyRepository[Comment, CommentCreate, CommentUpdate]):
    model = Comment
    _load_options: ClassVar[list[ExecutableOption]] = [
        selectinload(model.author),
        selectinload(model.news),
    ]

    async def get_multi(self, skip: int = 0, limit: int = 100, news_id: uuid.UUID | None = None) -> list[Comment]:
        """
        Получает список комментариев с возможностью фильтрации по news_id.
        """
        query = select(self.model)

        if news_id:
            query = query.where(self.model.news_id == news_id)

        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)

        if self._load_options:
            query = query.options(*self._load_options)

        result = await self.session.execute(query)
        return list(result.scalars().all())
