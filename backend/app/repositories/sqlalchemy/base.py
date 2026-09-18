import uuid
from typing import ClassVar, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption

from app.db.session import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class SQLAlchemyRepository[ModelType: Base, CreateSchemaType: BaseModel, UpdateSchemaType: BaseModel]:
    model: type[ModelType]
    _load_options: ClassVar[list[ExecutableOption]] = []

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, obj_id: uuid.UUID) -> ModelType | None:
        """Получает объект по ID с жадной загрузкой."""
        query = select(self.model).where(self.model.id == obj_id)
        if self._load_options:
            query = query.options(*self._load_options)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def create(self, data: CreateSchemaType) -> ModelType:
        """Создает объект."""
        db_obj = self.model(**data.model_dump())
        self.session.add(db_obj)
        await self.session.commit()
        result = await self.get_by_id(db_obj.id)
        assert result is not None  # Сужение типа для Mypy
        return result

    async def get_multi(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Получает список объектов."""
        query = select(self.model).order_by(self.model.id).offset(skip).limit(limit)
        if self._load_options:
            query = query.options(*self._load_options)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, db_obj: ModelType, update_data: UpdateSchemaType) -> ModelType:
        """Обновляет объект."""
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(db_obj, field, value)
        self.session.add(db_obj)
        await self.session.commit()
        result = await self.get_by_id(db_obj.id)
        assert result is not None
        return result

    async def delete(self, db_obj: ModelType) -> None:
        """Удаляет объект."""
        await self.session.delete(db_obj)
        await self.session.commit()
