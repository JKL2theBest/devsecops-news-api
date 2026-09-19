FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir "poetry>=2.4.3,<2.5.0"

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --without dev --no-interaction --no-ansi

COPY . .

CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
