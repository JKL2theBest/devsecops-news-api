import uuid
from typing import Any, TypeVar

from fastapi import HTTPException, status
from redis.asyncio import Redis

ModelType = TypeVar("ModelType")


class BaseService[ModelType]:
    def __init__(self, repository: Any, redis_client: Redis | None = None) -> None:
        self.repository = repository
        self.redis = redis_client

    async def get_by_id(self, obj_id: uuid.UUID) -> ModelType:
        db_obj = await self.repository.get_by_id(obj_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.repository.model.__name__} not found",
            )
        return db_obj
