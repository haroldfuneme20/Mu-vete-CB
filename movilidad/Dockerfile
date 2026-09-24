# Muévete CB — imagen única (API + PWA). Orden: ETL → build PWA → runtime (research R-02, T035).
# DATA_MODE=mock genera datos simulados si aún no hay archivos reales en data/raw/.

# --- 1) ETL: construye muevete.db y el paquete offline -------------------------------------
FROM python:3.12-slim AS etl
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
COPY backend/etl/requirements.txt backend/etl/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt -r backend/etl/requirements.txt
COPY backend backend
COPY agent agent
COPY data/raw data/raw
COPY data/seed data/seed
ARG DATA_MODE=real
RUN if [ "$DATA_MODE" = "mock" ]; then MOCK=--mock; else MOCK=; fi && \
    python -m backend.etl.build $MOCK --raw data/raw --seed data/seed \
      --db /out/muevete.db --offline /out/offline

# --- 2) PWA: el precache incluye el paquete offline ----------------------------------------
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY frontend ./
COPY --from=etl /out/offline ./public/offline
RUN npm run build

# --- 3) Runtime -----------------------------------------------------------------------------
FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    MUEVETE_DB=/app/data/build/muevete.db \
    MUEVETE_WORK_DB=/tmp/muevete.work.db \
    STATIC_DIR=/app/static \
    PHOTOS_DIR=/tmp/photos \
    LLM_PROVIDER=mock \
    PORT=8000
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt && \
    pip uninstall -y pytest ruff >/dev/null 2>&1 || true
COPY backend backend
COPY agent agent
COPY data/seed data/seed
COPY --from=etl /out/muevete.db data/build/muevete.db
COPY --from=web /web/dist static
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]
