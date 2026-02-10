FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

ENV UV_CACHE_DIR=/root/.cache/uv
ENV UV_HTTP_TIMEOUT=120

COPY requirements.txt /app/requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv uv pip install --system -r /app/requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend
RUN mkdir -p /app/data
COPY app.py /app/app.py

EXPOSE 8000 8501

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
