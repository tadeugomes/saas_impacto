# ── Build stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# Metadados
LABEL maintainer="SaaS Impacto Portuário"
LABEL description="Backend FastAPI + Celery Worker"

# Variáveis de ambiente para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependências do sistema (necessárias para psycopg2, cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# ── API target (default) ───────────────────────────────────────────────────
FROM base AS api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Worker target ──────────────────────────────────────────────────────────
FROM base AS worker
CMD ["celery", "-A", "app.tasks.celery_app.celery_app", "worker", \
     "--loglevel=info", "-Q", "economic_impact,celery", "-c", "2"]
