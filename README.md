# Full Stack Новостной портал

### 1. ЗАПУСК ПРОЕКТА

**Требования:**
- Python 3.12+
- Poetry (рекомендуется установка `pipx install poetry==2.4.3`)
- Docker & Docker Compose
- Node.js 24+ (LTS)

**Шаги для запуска:**

1.  Клонировать репозиторий:
    ```bash
    git clone https://github.com/JKL2theBest/devsecops-news-api.git
    cd devsecops-news-api
    ```
2. Создать `.env` файл в корне проекта, используя шаблон `.env.example`:
    ```bash
    cp .env.example .env
    ```
3. Установить зависимости (для бэкенда):
    ```bash
    cd backend
    poetry config virtualenvs.in-project true
    poetry env use 3.12
    poetry install
   ```
    3.1. Для установки зависимостей разработки (тесты, линтеры, форматтеры) используйте:
    ```bash
    poetry install --with dev
    ```
    3.2. Далее для автоматической проверки линтером при каждом коммите в корне проекта (`cd ../`) запустите:
    ```bash
    pipx install pre-commit
    pre-commit install
    ```
   Запуск автоматической проверки всех файлов проекта:
    ```bash
    pre-commit run --all-files
   ```
    > **Важно:** При внесении правок в `backend/pyproject.toml` или `.pre-commit-config.yaml` обязательно запускайте `pre-commit clean`, чтобы обновить кэш инструментов анализа.
4. Запуск проекта:
    ```bash
    docker compose up -d --build
    ```
5. Перед запуском тестов убедиться, что установлен браузер `playwright` (из папки `backend` (`cd backend`)):
    ```bash
    poetry run playwright install
    ```
6. Запуск тестов:
    ```bash
    poetry run pytest
    ```

Подробные инструкции по тестированию и демонстрации функционала можно найти в [документации проекта](./backend/README.md)
и отдельно про фронтенд [здесь](./frontend/README.md).
