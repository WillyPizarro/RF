FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
RUN pip install ".[dev]"

COPY . .

RUN useradd --create-home --uid 10001 api && chown -R api /app
USER api

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json', timeout=2)"

# Antes de servir: migraciones como dueño de las tablas y clave de api_app (app.migrar, ADR-0005).
CMD ["sh", "-c", "python -m app.migrar && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-config log_config.json --no-access-log"]
