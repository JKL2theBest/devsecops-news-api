from http import HTTPStatus

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_user_cannot_create_news(user_client: AsyncClient) -> None:
    """Тест: обычный пользователь не может создать новость."""
    response = await user_client.post(
        "/api/v1/news/",
        json={"title": "Forbidden Title", "content": {}},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


async def test_author_can_create_news(author_client: AsyncClient) -> None:
    """Тест: верифицированный автор может создать новость."""
    response = await author_client.post(
        "/api/v1/news/",
        json={"title": "Author's Title", "content": {"body": "text"}},
    )
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["title"] == "Author's Title"
    assert data["author"]["role"] == "verified_author"


async def test_get_news_unauthorized(client: AsyncClient) -> None:
    """Тест: неавторизованный пользователь не может получить список новостей."""
    response = await client.get("/api/v1/news/")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_get_news_authorized(user_client: AsyncClient) -> None:
    """Тест: авторизованный пользователь может получить список новостей."""
    response = await user_client.get("/api/v1/news/")
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json(), list)


@pytest.fixture
async def created_news(author_client: AsyncClient) -> dict:
    """Фикстура для создания новости для тестов обновления/удаления."""
    response = await author_client.post(
        "/api/v1/news/",
        json={"title": "Test News for Ownership", "content": {}},
    )
    assert response.status_code == HTTPStatus.CREATED
    return response.json()


async def test_author_can_update_own_news(author_client: AsyncClient, created_news: dict) -> None:
    """Тест: автор может обновить свою новость."""
    news_id = created_news["id"]
    response = await author_client.patch(f"/api/v1/news/{news_id}", json={"title": "Updated by Author"})
    assert response.status_code == HTTPStatus.OK
    assert response.json()["title"] == "Updated by Author"


async def test_author_can_delete_own_news(author_client: AsyncClient) -> None:
    """Тест: автор может удалить свою новость."""
    response = await author_client.post("/api/v1/news/", json={"title": "To Be Deleted", "content": {}})
    news_id = response.json()["id"]

    delete_response = await author_client.delete(f"/api/v1/news/{news_id}")
    assert delete_response.status_code == HTTPStatus.NO_CONTENT

    get_response = await author_client.get(f"/api/v1/news/{news_id}")
    assert get_response.status_code == HTTPStatus.NOT_FOUND


async def test_permissions_on_other_news(
    user_client: AsyncClient,
    author_client: AsyncClient,
    admin_client: AsyncClient,
) -> None:
    """Тест: юзер не может менять чужие новости, а админ может."""
    # 1. Автор создает новость
    response = await author_client.post("/api/v1/news/", json={"title": "Ownership Test", "content": {}})
    assert response.status_code == HTTPStatus.CREATED
    news_id = response.json()["id"]

    # 2. Обычный юзер пытается ее изменить (неуспешно)
    patch_response_user = await user_client.patch(f"/api/v1/news/{news_id}", json={"title": "Hacked Title"})
    assert patch_response_user.status_code == HTTPStatus.FORBIDDEN

    # 3. Админ пытается ее изменить (успешно)
    admin_patch_response = await admin_client.patch(f"/api/v1/news/{news_id}", json={"title": "Admin Updated"})
    assert admin_patch_response.status_code == HTTPStatus.OK
    assert admin_patch_response.json()["title"] == "Admin Updated"
