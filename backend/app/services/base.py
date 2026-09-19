from typing import TypeVar

from redis.asyncio import Redis

RepositoryType = TypeVar("RepositoryType")


class BaseService[RepositoryType]:
    def __init__(
        self,
        repository: RepositoryType,
        redis_client: Redis | None = None,
    ) -> None:
        self.repository = repository
        self.redis = redis_client
