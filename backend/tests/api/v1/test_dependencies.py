import uuid
from http import HTTPStatus

import pytest
from httpx import AsyncClient
from pytest_mock import MockerFixture

pytestmark = pytest.mark.asyncio


async def test_invalid_token_format(client: AsyncClient) -> None:
    """Тест: запрос с некорректным форматом токена возвращает 401."""
    headers = {"Authorization": "NotBearer at all"}
    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]


async def test_token_for_non_existent_user(client: AsyncClient, mocker: MockerFixture) -> None:
    """Тест: токен для удаленного/несуществующего юзера возвращает 401."""
    mocker.patch("jwt.decode", return_value={"sub": str(uuid.uuid4())})

    headers = {"Authorization": "Bearer some_valid_jwt_structure"}
    response = await client.get("/api/v1/users/", headers=headers)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "Could not validate credentials" in response.json()["detail"]
