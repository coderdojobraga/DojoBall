FROM python:3.12 AS builder

RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.8

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    poetry install --no-root --without dev

COPY src/ src/

FROM python:3.12-slim AS runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/src ./src

ENV SDL_VIDEODRIVER=dummy \
    PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "src/server.py"]
