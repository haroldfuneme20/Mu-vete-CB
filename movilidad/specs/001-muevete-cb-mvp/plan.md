# Implementation Plan: Muévete CB — MVP de movilidad comunitaria para Ciudad Bolívar

**Branch**: `001-muevete-cb-mvp` | **Date**: 2026-09-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-muevete-cb-mvp/spec.md`

## Summary

PWA mobile-first y accesible que recomienda viajes con al menos un extremo en Ciudad Bolívar
hacia cualquier localidad de Bogotá, combinando caminata, rutas comunitarias (simuladas),
SITP, TransMilenio y TransMiCable con ≤ 2 transbordos. Un motor determinístico en Python
(RAPTOR simplificado por frecuencias sobre el GTFS completo, preprocesado en SQLite) calcula y
ordena las alternativas; un agente LangGraph de 4 nodos interpreta texto libre y explica el
resultado con un proveedor LLM intercambiable (Mock por defecto). Los reportes ciudadanos
(con foto opcional) se capturan offline en IndexedDB, se sincronizan de forma idempotente y
penalizan tramos: 1 reporte parcial, 2+ confirmados invalidan. Todo se despliega como un único
contenedor (FastAPI sirve API + PWA) en Render mediante GitHub Actions.

## Technical Context

**Language/Version**: Python 3.12 (backend, agente, ETL); TypeScript 5 + React 18 (frontend)

**Primary Dependencies**: FastAPI, Pydantic v2, Uvicorn, LangGraph, httpx, Shapely 2,
PyYAML, rapidfuzz; ETL: pandas, pyogrio, pyproj. Frontend: Vite, vite-plugin-pwa (Workbox),
React Leaflet, MUI, idb

**Storage**: SQLite (archivo `muevete.db`, R\*Tree) en el servidor; IndexedDB en el teléfono;
fotos en disco efímero `/tmp/photos`

**Testing**: pytest + FastAPI TestClient; vitest; Lighthouse CI; ruff; eslint (+ jsx-a11y);
validación manual TalkBack/VoiceOver y modo avión

**Target Platform**: contenedor Linux en Render (512 MB RAM, disco efímero); navegadores
Chrome Android y Safari iOS

**Project Type**: aplicación web (monorepo: PWA + API + agente + ETL)

**Performance Goals**: recomendación < 5 s en el 95% de las consultas (objetivo interno
< 1 s de motor); arranque del contenedor ≤ 20 s; app offline abre en ≤ 3 s

**Constraints**: RSS ≤ 450 MB en pico; paquete offline ≤ 5 MB comprimido; sin API paga
obligatoria; sin login; WCAG 2.1 AA; ≤ 2 transbordos; LLM timeout 6 s → Mock

**Scale/Scope**: demo con decenas de usuarios simultáneos; datos de toda Bogotá (~8 000
paradas, ~2 000 patrones estimados); 6 pantallas (Inicio, Resultados, Detalle, Mapa, Reportar,
Estado/Offline)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio / sección (v2.2.2) | Cómo lo cumple el plan | Estado |
|---|---|---|
| I. La demo manda | Alcance = spec; sin login/perfil con cuenta; sin planificador multimodal completo; kill list respetada | ✅ |
| II. El motor decide, la IA explica | Motor Python puro con pipeline de 6 pasos, parámetros en `engine.yaml`, tests propios; LLM solo en `parse_request` (texto) y `explain_result`; validador de cifras; gazetteer resuelve lugares; LangGraph 4 nodos | ✅ |
| III. Offline-first real | Service Worker + paquete por niveles a/b/c + IndexedDB outbox; botón "Sincronizar ahora" + Background Sync opcional; mapa vectorial sin teselas; prueba en modo avión | ✅ |
| IV. Trazabilidad | Tabla `sources`, `source_id`/`source_ref` en toda fila, `source_kind` en cada tramo de la API, `demo_simulated` visible | ✅ |
| V. Proveedor intercambiable | `LLMProvider` + `FallbackProvider`; Mock por defecto; Gemini/Groq por HTTP; claves en Secrets | ✅ |
| VI. Retroalimentación ciudadana | Reporte anónimo con foto opcional sin EXIF; asociación a segmentos ≤ 100 m; regla 1 parcial / 2+ confirmados | ✅ |
| VII. Ciudad Bolívar ↔ Bogotá | Datos completos sin recorte; validación de extremo en Ciudad Bolívar; ≤ 2 transbordos | ✅ |
| VIII. Accesibilidad por lenguaje natural | Texto libre + respuesta natural; `aria-live`; descripción textual de rutas; formulario siempre disponible; Lighthouse ≥ 90 | ✅ |
| Stack y restricciones | React/Vite/Leaflet, FastAPI, LangGraph, SQLite + R\*Tree + Shapely, monorepo, un servicio, Dockerfile | ✅ |
| Fuentes de datos | ETL reproducible `data/raw` → `muevete.db` + paquete offline; WGS84; GTFS completo | ✅ |
| CI/CD y hosting | `ci.yml`, `deploy.yml` (GHCR → Render), `keepalive.yml`; respaldo HF Spaces | ✅ |
| Flujo y gates | Ramas main/dev/feature; gates 1–9 mapeados a historias; tests del motor | ✅ |

**Resultado pre-Phase 0**: PASA. **Re-check post-Phase 1** (tras data-model y contratos):
PASA — ver notas en Complexity Tracking (desviaciones menores justificadas, no violaciones).

## Project Structure

### Documentation (this feature)

```text
specs/001-muevete-cb-mvp/
├── plan.md              # Este archivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── api.md           # REST
│   ├── agent.md         # LangGraph + LLMProvider
│   └── offline-package.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
muevete-cb/
├── frontend/                      # PWA React + Vite + MUI + Leaflet
│   ├── public/
│   │   ├── manifest.webmanifest
│   │   └── offline/               # paquete offline generado por el ETL
│   ├── src/
│   │   ├── pages/                 # Home, Results, RouteDetail, Map, Report, Status
│   │   ├── components/            # AlternativeCard, RouteText, LiveAnswer, ConnectionBadge, LayerToggle
│   │   ├── map/                   # capas Leaflet, estilos formal/comunitario/incidente
│   │   ├── offline/               # idb stores, outbox, sync, photo compression
│   │   ├── services/              # cliente API
│   │   └── a11y/                  # tema MUI accesible, utilidades aria-live
│   └── tests/                     # vitest
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI: /api + estáticos de la PWA
│   │   ├── api/                   # routers: health, places, stops, routes, recommendations, reports, sync
│   │   ├── models/                # esquemas Pydantic (contratos)
│   │   ├── services/
│   │   │   ├── route_engine/      # motor determinístico (RAPTOR por frecuencias, scoring, incidentes)
│   │   │   ├── gazetteer.py
│   │   │   ├── reports.py         # persistencia, asociación a segmentos, confirmaciones
│   │   │   └── photos.py
│   │   └── db.py                  # SQLite + verificación R*Tree + carga del grafo
│   ├── config/                    # engine.yaml, fares.yaml
│   ├── etl/                       # build: data/raw → muevete.db + paquete offline
│   └── tests/
│       ├── unit/                  # motor (red de juguete), reglas de reportes, validador de cifras
│       ├── contract/              # respuestas de la API vs contracts/api.md
│       └── integration/           # escenarios A, B, E con datos de prueba
├── agent/
│   ├── graph.py                   # 4 nodos
│   ├── nodes/
│   ├── providers/                 # base, mock, gemini, groq, local (stub), fallback
│   ├── prompts/
│   └── tests/
├── data/
│   ├── raw/                       # originales (Git LFS para > 50 MB)
│   ├── seed/                      # community_routes.geojson, seed_reports.json, demo_scenarios.json, landmarks.json
│   └── build/                     # salida del ETL (ignorado en git)
├── docs/                          # architecture/, ux/, pitch/
├── .github/workflows/             # ci.yml, deploy.yml, keepalive.yml
├── Dockerfile                     # multi-etapa: ETL → node build (precache incluye offline/) → runtime python slim
├── README.md
└── .gitignore
```

**Structure Decision**: monorepo web con los directorios fijados por la constitución
(`frontend/`, `backend/`, `agent/`, `data/`, `docs/`). El ETL vive en `backend/etl/` para no
añadir un proyecto nuevo; `agent/` es un paquete Python importado por el backend en el mismo
proceso. El Dockerfile multi-etapa produce un único servicio.

## Mapeo historias → gates → componentes

| Historia | Gate(s) constitución | Componentes principales |
|---|---|---|
| US1 Recomendación | 1, 2, 3 | ETL, `route_engine`, `/api/recommendations`, Home/Results/RouteDetail |
| US2 Reporte cambia ranking | 4, 5 | `reports.py`, `photos.py`, `/api/reports`, Report |
| US3 Offline + sync | 6, 7 | Service Worker, `offline/`, `/api/sync`, Status |
| US4 Lenguaje natural accesible | 3 (texto), a11y | `agent/`, gazetteer, LiveAnswer, tema accesible |
| Mapa base (Phase 2b, antes de US1) | 2 | `map/MapView`, `/api/stops`, `/api/routes`, paquete offline |
| US5 Mapa completo (Phase 7) | — | alternativas, incidentes, "Ver en mapa" |
| US6 Fallback IA | — | `providers/fallback`, Mock |
| Deploy y demo | 8, 9 | Dockerfile, workflows, Render, keepalive |

## Riesgos técnicos y mitigación

| Riesgo | Mitigación |
|---|---|
| GTFS con estructura inesperada (sin `frequencies.txt`, `shapes.txt` incompletos) | ETL calcula headways desde `stop_times`; si falta `shapes`, línea recta entre paradas o malla vial (P-04) |
| Memoria > 512 MB | Grafo compacto, geometrías en SQLite; medir temprano (P-05); plan B HF Spaces |
| Primer reporte ya cambia la ruta en el Escenario B | Calibrar `partial.blockage.add_s` con datos reales (P-12); test de integración del escenario B |
| Nombres de lugares ambiguos | Gazetteer con localidad y pregunta de desambiguación (409) |
| iOS sin Background Sync | Botón "Sincronizar ahora" + evento `online` |
| Render dormido en el pitch | `keepalive.yml` + verificación `/api/health` + estado "Despertando…" |
| Límite de GitHub para archivos grandes | Git LFS o asset de Release (R-03) |

## Complexity Tracking

> No hay violaciones de la constitución. Se registran desviaciones menores justificadas.

| Desviación | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Rutas de la API con prefijo `/api/*` (la constitución lista `/routes`, `/reports`…) | La PWA y la API comparten dominio en un solo servicio; el prefijo evita choques con rutas del frontend | Sin prefijo, `/routes` colisiona con la navegación de la PWA y el Service Worker |
| Endpoints extra `/api/places` y `/api/reports/{id}/photo` | Autocompletar/desambiguación accesible (FR-009) y ver fotos (FR-014) | La API mínima es un piso, no un techo; sin ellos no se cumplen esos FR |
| RAPTOR simplificado (algoritmo de búsqueda) frente a "optimización compleja" fuera de alcance | La cobertura de toda Bogotá (VII) exige buscar combinaciones con transbordos | Comparar rutas precargadas no funciona con origen/destino libres; OTP es un planificador completo (prohibido) |
| Dependencias ETL pesadas (pandas, pyogrio, pyproj) | Leer GTFS y GeoJSON grandes y reproyectar | Se aíslan en la etapa de build de Docker; no entran en la imagen de ejecución |
