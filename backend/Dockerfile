FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

ENV UV_CACHE_DIR=/root/.cache/uv
ENV UV_HTTP_TIMEOUT=120

# Instalação rápida com uv + cache de layer
COPY requirements.txt /app/requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv uv pip install --system -r /app/requirements.txt

COPY src /app/src
COPY data /app/data

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
