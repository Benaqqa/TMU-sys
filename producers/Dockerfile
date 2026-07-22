# Build multi-stage: pas de gcc/libssl-dev/librdkafka-dev dans l'image finale
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends gcc libssl-dev librdkafka-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends librdkafka1 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /install /usr/local
WORKDIR /app
COPY producer_common.py producer_sap.py producer_oracle.py ./

USER appuser

# Pas de CMD implicite : chaque service du docker-compose.yml precise sa commande explicitement
