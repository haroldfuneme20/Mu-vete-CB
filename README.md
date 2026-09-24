# Muévete CB — Corredor Comunitario Inteligente

PWA mobile-first y accesible que recomienda viajes con al menos un extremo en **Ciudad Bolívar**
hacia cualquier localidad de Bogotá, integrando TransMiCable, TransMilenio, SITP y rutas
comunitarias, con reportes ciudadanos que funcionan **sin internet**.

- Constitución: [`.specify/memory/constitution.md`](.specify/memory/constitution.md)
- Especificación, plan y tareas: [`specs/001-muevete-cb-mvp/`](specs/001-muevete-cb-mvp/)
- Guía de validación: [`specs/001-muevete-cb-mvp/quickstart.md`](specs/001-muevete-cb-mvp/quickstart.md)

> **Estado de los datos:** mientras llegan los archivos oficiales, el proyecto funciona con datos
> **MOCK** generados por `backend/etl/mock_raw.py` (misma estructura que los reales). La API lo
> indica con `data_mode: "mock"` y la PWA muestra un aviso. Las rutas comunitarias son
> **simuladas para la demo** (`demo_simulated`).

## Arquitectura

```text
PWA (React + Vite + MUI + Leaflet, Service Worker, IndexedDB)
   │  REST /api/*
FastAPI ── LangGraph (4 nodos) ── LLMProvider (Mock | Gemini | Groq | Local)
   │              │
SQLite (R*Tree) ── Motor determinístico (RAPTOR por frecuencias, ≤ 2 transbordos)
```

El **motor decide** (reproducible, sin LLM); **la IA solo interpreta** texto libre y **explica**
con cifras validadas contra el resultado del motor.

## Estructura

| Carpeta | Contenido |
|---|---|
| `frontend/` | PWA |
| `backend/app/` | API FastAPI, motor de rutas, reportes |
| `backend/etl/` | `data/raw` → `muevete.db` + paquete offline |
| `backend/config/` | `engine.yaml` (parámetros del motor) y `fares.yaml` (tarifas) |
| `agent/` | Grafo LangGraph, proveedores LLM, prompts |
| `data/raw/` | Archivos originales ([README](data/raw/README.md)) |
| `data/seed/` | Rutas comunitarias simuladas, reportes semilla, escenarios, hitos |
| `docs/` | Arquitectura, despliegue y pitch |

## Desarrollo local

Requisitos: Python 3.12+, Node.js 20+.

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt -r backend/etl/requirements.txt

# 1) Datos (mock mientras no estén los reales; quitar --mock con datos reales)
python -m backend.etl.build --mock --offline frontend/public/offline

# 2) API
uvicorn backend.app.main:app --port 8000

# 3) PWA (otra terminal; /api se redirige a :8000)
cd frontend && npm install && npm run dev
```

## Pruebas

```bash
ruff check . && pytest -q                  # motor, reglas de reportes, contratos, escenarios A/B/E/F
cd frontend && npm run lint && npm test    # outbox, sincronización, compresión de fotos
```

## Imagen Docker (igual a producción)

```bash
docker build --build-arg DATA_MODE=mock -t muevete-cb .
docker run --rm -p 8000:8000 -m 512m muevete-cb
```

## Despliegue

GitHub Actions: `ci.yml` (PR), `deploy.yml` (push a `main` → GHCR → Render), `keepalive.yml`
(evento). Ver [`docs/deploy/render.md`](docs/deploy/render.md) y el respaldo
[`docs/deploy/hf-spaces.md`](docs/deploy/hf-spaces.md).

Variables: `LLM_PROVIDER` (`mock` por defecto), `GEMINI_API_KEY`, `GROQ_API_KEY` (GitHub Secrets o
variables de Render; nunca en el repo), `DEMO_B_BACKUP=true` para precargar el primer bloqueo del
Escenario B.
