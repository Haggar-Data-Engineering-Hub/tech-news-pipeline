# ── Stage 1 : dépendances ────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Installer les dépendances système nécessaires à snowflake-connector
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2 : image finale légère ────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copier les packages installés depuis le builder
COPY --from=builder /install /usr/local

# Copier le code source
COPY ingestion/ ingestion/
COPY flows/     flows/
COPY db/        db/

# Variables d'environnement par défaut (surchargées via --env-file ou docker-compose)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Point d'entrée : lancer le flow Prefect
CMD ["python", "main.py"]
