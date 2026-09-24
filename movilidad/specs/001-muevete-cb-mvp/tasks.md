---

description: "Task list for Muévete CB MVP"
---

# Tasks: Muévete CB — MVP de movilidad comunitaria para Ciudad Bolívar

**Input**: Design documents from `specs/001-muevete-cb-mvp/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluidos solo donde la constitución los exige (motor determinístico, reproducibilidad,
regla de reportes, contratos, fallback IA, outbox) y para los escenarios de demo A, B y E.
No se aplica TDD estricto al resto.

**Organization**: tareas agrupadas por historia de usuario (spec.md). Entre paréntesis al final
de cada fase se sugiere el rol responsable: Backend, Frontend, GIS (analista territorial),
Arquitectura (agente/seguridad/deploy).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia a la que pertenece (US1…US6)
- Rutas relativas a la raíz del monorepo (ver plan.md → Project Structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: inicializar el monorepo y las herramientas (Arquitectura + todos)

- [ ] T001 Inicializar git (`main` y `dev`), crear el árbol de directorios de plan.md (`frontend/`, `backend/app/`, `backend/config/`, `backend/etl/`, `backend/tests/{unit,contract,integration}/`, `agent/{nodes,providers,prompts,tests}/`, `data/{raw,seed,build}/`, `docs/{architecture,ux,pitch,deploy}/`, `.github/workflows/`) y `.gitignore` en la raíz (ignorar `data/build/`, `node_modules/`, `__pycache__/`, `.env`, `frontend/dist/`, `frontend/public/offline/*.geojson`) — ⏸ estructura e ignores creados; `git init`/ramas omitidos por indicación del usuario (se hará commit a un repo existente)
- [X] T002 Configurar Git LFS en `.gitattributes` para `data/raw/**/*.zip` y `data/raw/**/*.geojson` (research R-03)
- [X] T003 [P] Crear `pyproject.toml` en la raíz con configuración de ruff (line-length 100) y pytest (`testpaths = ["backend/tests", "agent/tests"]`)
- [X] T004 [P] Crear `backend/requirements.txt` (fastapi, uvicorn[standard], pydantic>=2, python-multipart, httpx, shapely>=2, pyyaml, rapidfuzz, langgraph, pytest, ruff)
- [X] T005 [P] Crear `backend/etl/requirements.txt` (pandas, pyogrio, shapely>=2, pyproj, pyyaml)
- [X] T006 [P] Inicializar el frontend con Vite + React + TypeScript en `frontend/` e instalar `@mui/material @emotion/react @emotion/styled react-router-dom leaflet react-leaflet idb vite-plugin-pwa` y dev `vitest eslint eslint-plugin-jsx-a11y @lhci/cli` en `frontend/package.json`
- [X] T007 [P] Configurar ESLint con `jsx-a11y` (recomendado) en `frontend/eslint.config.js`
- [ ] T008 [P] Crear `data/raw/README.md` con la lista de archivos esperados (BarriosCatastrales, trazado troncal, rutas provisionales, paraderos zonales SITP, estaciones TM, malla vial integrada, GTFS zip), nombre de archivo, atributos requeridos y CRS de cada uno (pendientes P-03/P-04) y colocar los archivos reales — ⏸ `data/raw/README.md` listo; archivos reales pendientes (se usan datos MOCK de `backend/etl/mock_raw.py`)
- [X] T009 [P] Copiar los diagramas de `documentacion/` a `docs/architecture/` y crear `README.md` raíz con descripción, estructura y enlaces a `specs/001-muevete-cb-mvp/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: datos, servidor, agente mínimo, shell de la PWA y despliegue continuo. Cubre el
**Gate 1** (PWA abre en el teléfono).

**⚠️ CRITICAL**: ninguna historia empieza hasta terminar esta fase

### Configuración y esquema

- [X] T010 Crear `backend/config/engine.yaml` con exactamente los valores de data-model.md §2 (walk, transfers, wait, candidates, reports.partial/confirmed/caps, weights, tie_break)
- [X] T011 [P] Crear `backend/config/fares.yaml` con claves `tm_troncal`, `transmicable`, `sitp_zonal`, `integrated_transfer` y `community` (valores marcados `# POR CONFIRMAR P-06`)
- [X] T012 Implementar `backend/app/config.py`: settings por variables de entorno (`MUEVETE_DB`, `LLM_PROVIDER`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `PHOTOS_DIR=/tmp/photos`, `STATIC_DIR`, `DEMO_B_BACKUP`) y carga validada de `engine.yaml` y `fares.yaml`
- [X] T013 Crear `backend/etl/schema.sql` con las tablas `sources`, `barrios`, `stops`, `patterns`, `pattern_stops`, `segments`, `footpaths`, `gazetteer`, `reports`, `report_segments` y las tablas virtuales R*Tree `barrios_rtree`, `stops_rtree`, `segments_rtree` (data-model.md §1)

### ETL (GIS + Backend)

- [X] T014 Implementar `backend/etl/common.py`: lectura con pyogrio, reproyección a EPSG:4326, cálculo de distancias en EPSG:3116, normalización de nombres (minúsculas, sin tildes ni prefijos), registro en `sources`, y error claro si falta un archivo o atributo
- [X] T015 [P] Implementar `backend/etl/load_barrios.py`: cargar BarriosCatastrales, calcular `is_ciudad_bolivar` desde el atributo de localidad (nombre configurable), centroides, WKB y `barrios_rtree`
- [X] T016 [P] Implementar `backend/etl/load_stops.py`: cargar paraderos zonales SITP, estaciones TM/TransMiCable y `stops.txt` del GTFS; fusionar duplicados ≤ 15 m con nombre similar conservando `source_ref`; asignar `barrio_id`; poblar `stops_rtree`
- [X] T017 Implementar `backend/etl/load_gtfs.py`: construir `patterns` (route_id + secuencia de paradas) y `pattern_stops` con tiempos acumulados medianos desde `stop_times.txt`; headways pico/valle desde `frequencies.txt` o calculados desde salidas; ventana de servicio; `mode` según tipo de ruta; `reliability`/`confidence` institucionales (depende de T016)
- [X] T018 [P] Implementar `backend/etl/load_tm_lines.py`: cargar trazado troncal y rutas provisionales (marcar `mode = provisional`) para geometría de tramos troncales
- [X] T019 Implementar `backend/etl/build_segments.py`: geometría de cada par de paradas consecutivas desde `shapes.txt`, trazado troncal o línea recta como respaldo; poblar `segments` y `segments_rtree` (depende de T017, T018)
- [X] T020 Implementar `backend/etl/build_footpaths.py`: transbordos a pie entre paradas a ≤ 250 m con `walk_s` a 4,5 km/h usando `stops_rtree` (depende de T016)
- [X] T021 Implementar `backend/etl/build_gazetteer.py` y crear `data/seed/landmarks.json` (al menos "Av. Jiménez", "Centro", "Portal Tunal") con nombres normalizados de barrios, estaciones y paraderos + localidad (depende de T015, T016)
- [X] T022 Implementar `backend/etl/build.py` (CLI `python -m backend.etl.build --raw --seed --db --offline`): ejecutar T014–T021 en orden, imprimir conteos (barrios totales y de Ciudad Bolívar, paradas, patrones, segmentos, footpaths) y escribir `data_version`
- [X] T022b Implementar `backend/etl/export_offline.py` (niveles a y b): nivel a con Ciudad Bolívar (barrios, paradas y estaciones, vías principales de la malla vial filtradas por jerarquía, rutas comunitarias simuladas cuando existan) y `places_index.json`; nivel b con trazado troncal y estaciones TM/TransMiCable de toda Bogotá; simplificación (~5 m y ~15 m), solo atributos `id`, `name`, `kind`, `source_kind`; `manifest.json` con versión y tamaños y verificación ≤ 5 MB comprimido (contracts/offline-package.md); integrarlo en `backend/etl/build.py` con la opción `--offline` (depende de T022)

### Servidor base

- [X] T023 Implementar `backend/app/db.py`: copiar `muevete.db` a un archivo de trabajo al arrancar, verificar soporte R*Tree (fallar con mensaje claro), conexión por request y `data_version`
- [X] T024 Implementar `backend/app/services/route_engine/graph.py`: cargar en memoria estructuras compactas (patrones, paradas por patrón con tiempos, headways, footpaths, índice parada→patrones) desde SQLite
- [X] T025 [P] Crear `backend/app/models/common.py` con Pydantic: `ErrorBody`, `PlaceRef` (ref_id | lat/lng), `Place`, `Evidence` (contracts/api.md)
- [X] T026 Implementar `backend/app/api/errors.py`: excepciones de dominio (`OUT_OF_COVERAGE`, `SAME_ORIGIN_DESTINATION`, `AMBIGUOUS_PLACE`, `NO_ROUTE`, `PAYLOAD_TOO_LARGE`, `VALIDATION_ERROR`) y handler con la forma común de error
- [X] T027 Implementar `backend/app/main.py`: app FastAPI, lifespan (T023, T024), router `/api`, servir `STATIC_DIR` (build de la PWA) con fallback a `index.html` para rutas del SPA
- [X] T028 Implementar `GET /api/health` en `backend/app/api/health.py` (status, data_version, llm_provider, reports_active, uptime_s)

### Agente mínimo (constitución V: Mock desde el inicio)

- [X] T029 [P] Crear `agent/providers/base.py` con el protocolo `LLMProvider` (`name`, `generate(prompt) -> str`) y `agent/providers/mock.py` con `MockProvider` determinístico (sin red; métodos de plantilla que se completan en US1 y US4)
- [X] T029b Implementar `agent/providers/fallback.py` (`FallbackProvider(primary, MockProvider)`, timeout 6 s, cualquier excepción o salida inválida → Mock, registra el motivo en log) y la fábrica mínima `agent/providers/__init__.py` (`LLM_PROVIDER`, por defecto `mock`) (depende de T029)
- [X] T030 [P] Crear `agent/state.py` con `AgentState` (contracts/agent.md)

### PWA base

- [X] T031 [P] Crear el tema accesible en `frontend/src/a11y/theme.ts` (tipografía base 16 px en rem, contraste AA, `minHeight/minWidth` 44 px en botones) y `frontend/src/a11y/announce.ts` (utilidad para `aria-live`)
- [X] T032 Crear `frontend/src/App.tsx` y `frontend/src/main.tsx` con react-router: rutas `/` (Inicio), `/resultados`, `/ruta/:id`, `/mapa`, `/reportar`, `/estado`; layout con barra inferior accesible (Inicio, Mapa, Reportar, Estado; **sin Perfil**) en `frontend/src/components/Layout.tsx`
- [X] T033 [P] Implementar `frontend/src/services/api.ts`: cliente `fetch` para `/api/*` con manejo de la forma de error común y estado "Despertando el servicio…" si `/api/health` tarda > 2 s
- [X] T034 Configurar `vite-plugin-pwa` en `frontend/vite.config.ts` (precache del app shell, proxy `/api` → `:8000` en dev) y `frontend/public/manifest.webmanifest` (nombre Muévete CB, íconos, `display: standalone`)

### Despliegue continuo

- [X] T035 Crear `Dockerfile` multi-etapa en la raíz: (1) `python:3.12` con `backend/requirements.txt` + `backend/etl/requirements.txt` ejecuta `python -m backend.etl.build` sobre `data/raw` + `data/seed` → `muevete.db` + `offline/`; (2) `node:20` copia `offline/` a `frontend/public/offline/` y ejecuta el build de la PWA (el precache incluye el paquete offline); (3) `python:3.12-slim` runtime con `backend/requirements.txt`, `backend/`, `agent/`, `muevete.db`, `data/seed/` y `frontend/dist` → `STATIC_DIR`; `CMD uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- [X] T036 [P] Crear `.github/workflows/ci.yml`: en PR a `dev`/`main` → checkout con `lfs: true` (+ descarga del GTFS desde el asset del Release si no está en LFS, research R-03), `ruff check`, `pytest`, `npm ci && npm run lint && npm test && npm run build`
- [X] T037 Crear `.github/workflows/deploy.yml`: en push a `main` → checkout con `lfs: true` (+ descarga del GTFS desde el asset del Release si aplica), build de la imagen, push a GHCR (`ghcr.io/<org>/muevete-cb`), `curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}` y verificación de `/api/health` con reintentos; crear el Web Service en Render apuntando a la imagen de GHCR — ✔ workflow listo; crear el Web Service en Render y los secretos según `docs/deploy/render.md`
- [X] T038 Crear `backend/tests/conftest.py` con fixture de **red de juguete**: base SQLite temporal creada con `backend/etl/schema.sql` con ~12 paradas, 4 patrones (1 transmicable, 1 troncal, 1 zonal, 1 comunitario `demo_simulated`), footpaths y segmentos; y `TestClient` apuntando a ella
- [ ] T038b Con la base real de T022, ejecutar `docker run -m 512m` y medir RSS en reposo y tiempo de arranque; registrar en `docs/architecture/memory.md`. Si RSS > 300 MB en reposo, activar el plan B (`docs/deploy/hf-spaces.md`) antes de US1 (P-05) — ⏸ línea base con datos MOCK: 92 MB RSS, arranque 9 s (`docs/architecture/memory.md`); falta medir con datos reales en `docker run -m 512m`

**Checkpoint (Gate 1)**: `docker run -m 512m` arranca, RSS medido y dentro del presupuesto, `/api/health` = ok, la PWA abre en un teléfono desde la URL de Render.

---

## Phase 2b: Mapa base (Gate 2) — primera parte de US5

**Goal**: cumplir el Gate 2 ("mapa y datos cargan") antes de construir la recomendación: capas de Ciudad Bolívar, estaciones y troncales, en línea y sin conexión. Dibujar la ruta recomendada llega en US1 (T059) y el resto del mapa en la Phase 7.

**Independent Test**: abrir el mapa en el teléfono desde la URL de Render y ver Ciudad Bolívar, estaciones y troncales con leyenda formal/comunitaria; en modo avión se ve sobre fondo neutro.

- [X] T099 [P] [US5] Implementar `GET /api/stops` (bbox, kind, máx. 2 000) en `backend/app/api/stops.py` y `GET /api/routes`, `GET /api/routes/{id}` en `backend/app/api/routes.py`, con test de contrato en `backend/tests/contract/test_map_contract.py`
- [X] T100 [US5] Implementar `frontend/src/pages/Map.tsx`, `frontend/src/map/layers.ts` y el componente reutilizable `frontend/src/map/MapView.tsx`: Leaflet con teselas OSM (atribución) en línea y fondo neutro sin conexión; capas de Ciudad Bolívar, estaciones y troncales desde el paquete offline (T022b) y la API (T099); lo reutilizan T059 y `LocationPicker` en T073
- [X] T101 [P] [US5] Implementar `frontend/src/map/styles.ts` (formal, comunitaria simulada con trazo discontinuo, incidente por categoría, recomendada resaltada), `frontend/src/components/LayerToggle.tsx` y `frontend/src/components/Legend.tsx`

**Checkpoint (Gate 2)**: mapa y datos cargan en el teléfono (en línea y en modo avión), sobre la URL de Render.

---

## Phase 3: User Story 1 - Obtener una recomendación de ruta explicada (Priority: P1) 🎯 MVP

**Goal**: origen/destino/prioridad por formulario → hasta 3 alternativas determinísticas con métricas, fuente, evidencia y explicación.

**Independent Test**: Escenario A (Mirador del Paraíso → Av. Jiménez, "más rápido") devuelve alternativas completas; repetir 3 veces da el mismo orden; la ruta se dibuja en el mapa. (Gate 3)

### Tests for User Story 1

- [X] T039 [P] [US1] Tests del motor sobre la red de juguete en `backend/tests/unit/test_route_engine.py`: acceso a pie ≤ 600 m, espera = headway/2, máximo 2 transbordos, penalización de transbordo, fuera de horario → sin resultado, desempate (tiempo, id), misma entrada → mismo orden e `id`
- [X] T040 [P] [US1] Tests de scoring en `backend/tests/unit/test_scoring.py`: normalización min-max, cada perfil de `weights` cambia el orden esperado, top-3
- [X] T041 [P] [US1] Test del validador de cifras de la explicación en `agent/tests/test_explain_validator.py` (rechaza números ausentes en los hechos; acepta los presentes)
- [X] T042 [P] [US1] Test de contrato de `POST /api/recommendations` (formulario) y `GET /api/places` en `backend/tests/contract/test_recommendations_contract.py`: forma de respuesta, `source_kind` en cada leg, errores `OUT_OF_COVERAGE`, `SAME_ORIGIN_DESTINATION`, `NO_ROUTE`

### Implementation for User Story 1

- [X] T043 [P] [US1] Crear `backend/app/models/recommendation.py`: `RecommendationRequest` (origin/destination o query, priority, depart_at), `Leg`, `Alternative`, `Recommendation` (contracts/api.md)
- [X] T044 [P] [US1] Implementar `backend/app/services/gazetteer.py`: resolver `ref_id` o lat/lng a `Place` (barrio contenedor, `is_ciudad_bolivar`), búsqueda difusa con rapidfuzz y umbral, lista de candidatos para desambiguar
- [X] T045 [US1] Implementar `backend/app/services/route_engine/access.py`: paradas a distancia caminable del origen/destino con tiempo a pie (usa `stops_rtree` + Shapely)
- [X] T046 [US1] Implementar `backend/app/services/route_engine/raptor.py`: RAPTOR por frecuencias con 3 rondas, footpaths, ventana de servicio según `depart_at`, punteros para reconstruir caminos y extracción de hasta `k_search` candidatos distintos (research R-01)
- [X] T047 [US1] Implementar `backend/app/services/route_engine/metrics.py`: tiempo total (caminata + espera + viaje + transbordos), costo con `fares.yaml` y regla de transbordo integrado, disponibilidad, confiabilidad y confianza por candidato
- [X] T048 [US1] Implementar `backend/app/services/route_engine/scoring.py`: normalización, pesos por prioridad, desempate `tie_break`, top `k_return`
- [X] T049 [US1] Implementar `backend/app/services/route_engine/describe.py`: `text_description` en español sencillo de cada alternativa (paradas en orden, minutos, costo, confianza, "simulada para la demo" si aplica) — FR-012
- [X] T050 [US1] Implementar `backend/app/services/route_engine/engine.py`: pipeline de 6 pasos (resolver → candidatos → métricas → incidentes [lista vacía por ahora] → score → devolver con evidencia), `id` determinístico por hash de patrones, validación de extremo en Ciudad Bolívar y origen ≠ destino; distinguir alternativas *invalidadas* (se excluyen; si no queda ninguna → `NO_ROUTE` con sugerencia de otra hora/prioridad) de *penalizadas* (si todas las viables tienen penalización, se marca `warning: "all_affected"`)
- [X] T051 [US1] Implementar nodos `agent/nodes/parse_request.py` (camino de formulario: solo resolver lugares), `agent/nodes/retrieve_mobility_data.py` (data_version, reportes activos vacíos), `agent/nodes/evaluate_routes.py` (llama a `engine.py`) y `agent/graph.py` con las aristas de contracts/agent.md
- [X] T052 [US1] Implementar `agent/nodes/explain_result.py`, `agent/validators.py` (validador de cifras) y `agent/prompts/explain.txt`; completar la plantilla determinística de explicación en `agent/providers/mock.py`
- [X] T053 [US1] Implementar `POST /api/recommendations` (formulario) en `backend/app/api/recommendations.py` y `GET /api/places` en `backend/app/api/places.py`, invocando el grafo del agente
- [X] T054 [P] [US1] Diseñar ≥ 3 rutas comunitarias simuladas sobre malla vial y paradas reales (al menos una alimenta Mirador del Paraíso o Juan Pablo II) en `data/seed/community_routes.geojson` con paradas, costo, frecuencia, horario, confianza 0,5–0,6, fecha y `source_kind = demo_simulated` (P-02a, GIS) — ✔ 3 rutas simuladas sobre paradas MOCK; reubicar sobre paradas reales al cargar datos (P-02a)
- [X] T055 [US1] Implementar `backend/etl/load_community.py` (patrones `community` desde T054), integrarlo en `backend/etl/build.py` y volver a exportar el nivel a del paquete offline (T022b) para incluir `community_routes.geojson`
- [X] T056 [P] [US1] Crear `data/seed/demo_scenarios.json` con los escenarios A (Mirador del Paraíso → Av. Jiménez, `fast`) y F (Barrio Paraíso → Portal Tunal, `reliable`)
- [X] T057 [P] [US1] Implementar la página Inicio en `frontend/src/pages/Home.tsx` con `frontend/src/components/PlaceField.tsx` (autocompletar con `/api/places` y, sin conexión, con `/offline/places_index.json`; etiqueta accesible) y `frontend/src/components/PriorityPicker.tsx` (Más rápido / Más económico / Más confiable; sin selección = "Balanceado", anunciado al lector de pantalla) y botón "Buscar rutas"
- [X] T058 [P] [US1] Implementar `frontend/src/pages/Results.tsx` con `frontend/src/components/AlternativeCard.tsx` (tiempo, costo, confianza, transbordos, tipos de transporte), `frontend/src/components/SourceBadge.tsx` (institucional / "simulada para la demo") y aviso accesible cuando la respuesta trae `warning: "all_affected"`
- [X] T059 [US1] Implementar `frontend/src/pages/RouteDetail.tsx` con `frontend/src/components/RouteText.tsx` (tramos y paradas en orden), explicación, evidencia, fecha de actualización y botón "Ver en mapa" que abre `MapView` (T100) con la ruta recomendada resaltada y las alternativas (estilos de T101)
- [X] T060 [US1] Test de integración del Escenario A en `backend/tests/integration/test_scenario_a.py` (usa `data/build/muevete.db` si existe; `skip` si no): ≥ 2 alternativas viables, mismo orden en 3 ejecuciones, y 20 consultas de los escenarios A y F con percentil 95 < 5 s (SC-002)

**Checkpoint (Gate 3)**: el Escenario A funciona de punta a punta en la URL de Render y su ruta se dibuja en el mapa.

---

## Phase 4: User Story 2 - Reportar una contingencia y ver cambiar la recomendación (Priority: P2)

**Goal**: reporte anónimo (foto opcional) que penaliza tramos: 1 reporte parcial; 2+ de dispositivos distintos invalidan (bloqueo).

**Independent Test**: Escenario B — primer bloqueo penaliza, segundo desde otro teléfono cambia la recomendación y la explicación dice "2 personas reportaron". (Gates 4 y 5)

### Tests for User Story 2

- [X] T061 [P] [US2] Tests de reglas en `backend/tests/unit/test_report_rules.py`: 1 reporte → parcial; 2 `anon_id` distintos → bloqueo invalida; mismo `anon_id` cuenta 1; vencido (2 h desde `received_at`) no afecta; reporte > 100 m no afecta; topes `caps`
- [X] T062 [P] [US2] Test de contrato de `POST /api/reports`, `GET /api/reports`, `GET /api/reports/{id}/photo` en `backend/tests/contract/test_reports_contract.py`: 201 nuevo, 200 `duplicate`, 413 foto > 1 MB, 422 sin ubicación/categoría, `anon_id` nunca expuesto
- [X] T063 [P] [US2] Test de integración del Escenario B en `backend/tests/integration/test_scenario_b.py` sobre la red de juguete y, si existe, la base real

### Implementation for User Story 2

- [X] T064 [P] [US2] Crear `backend/app/models/report.py`: `ReportIn`, `ReportOut`, `ReportPublic` (sin `anon_id`), categorías y límites (descripción ≤ 280)
- [X] T065 [US2] Implementar `backend/app/services/reports.py`: upsert idempotente por `id`, `received_at`/`expires_at`, asociación a segmentos ≤ 100 m (`segments_rtree` + Shapely) en `report_segments`, conteo de confirmaciones por segmento/categoría con `anon_id` distintos, consulta de reportes activos
- [X] T066 [P] [US2] Implementar `backend/app/services/photos.py`: validar `image/jpeg` ≤ 1 MB, guardar en `PHOTOS_DIR`, servir por id
- [X] T067 [US2] Implementar `backend/app/services/route_engine/incidents.py` (penalización parcial/confirmada con topes según `engine.yaml`) y conectarlo en el paso 4 de `backend/app/services/route_engine/engine.py`; `agent/nodes/retrieve_mobility_data.py` ahora carga los reportes activos
- [X] T068 [US2] Implementar `POST /api/reports` (multipart `report` + `photo`), `GET /api/reports?active&bbox` y `GET /api/reports/{id}/photo` en `backend/app/api/reports.py`
- [X] T069 [US2] Actualizar `agent/nodes/explain_result.py` y la plantilla de `agent/providers/mock.py` para citar reportes ("1 persona reportó…", "2 personas reportaron…") y su efecto
- [X] T070 [US2] Implementar `backend/app/services/seed.py`: cargar `data/seed/seed_reports.json` al arrancar (restaurar estado de demo, FR-033), incluido el reporte de respaldo del Escenario B activado solo con `DEMO_B_BACKUP=true`
- [X] T071 [P] [US2] Implementar `frontend/src/offline/db.ts` (IndexedDB con `idb`: stores `outbox`, `results`, `meta`, `prefs`) y `frontend/src/offline/identity.ts` (`anon_id` UUID persistente)
- [X] T072 [P] [US2] Implementar `frontend/src/offline/photo.ts` (canvas lado mayor ≤ 1280 px, JPEG 0,7 → 0,5, rechazo si > 1 MB; elimina EXIF) con test en `frontend/tests/photo.test.ts`
- [X] T073 [US2] Implementar `frontend/src/pages/Report.tsx` con `frontend/src/components/CategoryPicker.tsx` (Bloqueo, Retraso, Cambio de ruta, Riesgo, Otro), `frontend/src/components/LocationPicker.tsx` (ubicación actual o punto en el mapa usando `MapView` de T100), descripción opcional y botón "Agregar foto (opcional)" con etiqueta accesible y aviso "No incluyas rostros ni placas en la foto"; envío en línea a `POST /api/reports`
- [X] T074 [US2] Mostrar en `frontend/src/components/AlternativeCard.tsx` y `frontend/src/pages/RouteDetail.tsx` los reportes que afectan cada tramo (categoría, confirmaciones, efecto) y refrescar la recomendación tras enviar un reporte
- [X] T075 [US2] Calibrar `reports.partial.blockage` en `backend/config/engine.yaml` con los datos reales del Escenario A para que el primer reporte **no** cambie la recomendación y el segundo sí; documentar valores en `data/seed/demo_scenarios.json` (P-12) — ✔ calibrado y verificado con MOCK (44 → 59 min con 1 reporte; cambia con 2); recalibrar con datos reales

**Checkpoint (Gates 4–5)**: Escenario B reproducible con dos teléfonos.

---

## Phase 5: User Story 3 - Reportar sin conexión y sincronizar después (Priority: P3)

**Goal**: app abre offline con el paquete por niveles, guarda reportes (con foto) en el outbox y sincroniza de forma idempotente.

**Independent Test**: Escenarios C y D en modo avión en un teléfono real. (Gates 6 y 7)

### Tests for User Story 3

- [X] T076 [P] [US3] Tests del outbox en `frontend/tests/outbox.test.ts` (fake-indexeddb): persistencia, `syncing` interrumpido vuelve a `pending_sync`, `accepted`/`duplicate` → `synced`, `rejected` → `error`
- [X] T077 [P] [US3] Test de contrato de `POST /api/sync` en `backend/tests/contract/test_sync_contract.py`: lote ≤ 20, resultados por reporte, reenvío del mismo lote sin duplicados, `recalculate`

### Implementation for User Story 3

- [X] T078 [US3] Implementar `POST /api/sync` en `backend/app/api/sync.py` (multipart `reports` + `photo_<id>`, reutiliza `backend/app/services/reports.py` y `photos.py`)
- [X] T079 [US3] Ampliar `backend/etl/export_offline.py` (creado en T022b) con el **nivel c**: recomendaciones precalculadas de los escenarios A y F para cada prioridad, generadas con `backend/app/services/route_engine/engine.py` y guardadas en `demo_scenarios.json`; actualizar `manifest.json`
- [X] T080 [US3] Ampliar `frontend/vite.config.ts` para precachear `/offline/**` y caché en tiempo de ejecución limitada de teselas ya vistas; implementar `frontend/src/offline/package.ts` (versión del manifest, actualización en segundo plano sin tocar el outbox)
- [X] T081 [US3] Implementar `frontend/src/offline/outbox.ts`: guardar reporte + Blob, estados (draft → pending_sync → syncing → synced/error), `attempts`, manejo de cuota de almacenamiento llena con aviso
- [X] T082 [US3] Implementar `frontend/src/offline/sync.ts`: lotes de 20 a `/api/sync`, disparo por botón, evento `online` y Background Sync donde exista; actualiza `meta.last_sync_at` y pide recálculo si `recalculate`
- [X] T083 [US3] Actualizar `frontend/src/pages/Report.tsx`: sin conexión guarda en el outbox y anuncia "Guardado localmente. Pendiente de sincronización" (aria-live)
- [X] T084 [P] [US3] Implementar `frontend/src/components/ConnectionBadge.tsx` (Conectado / Sin conexión + contador de pendientes) e integrarlo en `frontend/src/components/Layout.tsx`
- [X] T085 [US3] Implementar `frontend/src/pages/Status.tsx`: estado de conexión, hora de última sincronización, lista de pendientes con su estado y botón "Sincronizar ahora"
- [X] T086 [US3] Implementar `frontend/src/services/recommendations.ts`: guardar cada `Recommendation` en `results`; sin conexión servir el resultado guardado de la misma consulta o del escenario precalculado equivalente (nivel c) indicando la fecha del cálculo; si no existe, aviso accesible de que requiere conexión y cola de consultas pendientes que se ejecutan al reconectar (FR-010)

**Checkpoint (Gates 6–7)**: modo avión → reporte guardado → reabrir → reconectar → sincronizado sin duplicados.

---

## Phase 6: User Story 4 - Consultar en lenguaje natural con accesibilidad (Priority: P4)

**Goal**: texto libre → interpretación (LLM o reglas) → gazetteer → recomendación → respuesta natural anunciada por el lector de pantalla.

**Independent Test**: Escenario F con TalkBack/VoiceOver sin mirar la pantalla; ≥ 18/20 frases correctas.

### Tests for User Story 4

- [X] T087 [P] [US4] Crear `agent/tests/fixtures/nl_phrases.json` con 20 frases de prueba y su interpretación esperada (P-08) y `agent/tests/test_parse_request.py` (≥ 18 correctas con Mock; ambiguas → clarificación; fuera de tema → `off_topic`)
- [X] T088 [P] [US4] Test de contrato de la variante `query` de `POST /api/recommendations` en `backend/tests/contract/test_recommendations_nl_contract.py` (200 con `interpreted_from_text`, 409 `AMBIGUOUS_PLACE` con candidatos, 422 `off_topic`)

### Implementation for User Story 4

- [X] T089 [US4] Completar el parser por reglas en `agent/providers/mock.py` ("de X a Y", "desde X hasta Y", "ir a Y desde X", palabras de prioridad rápido/barato/económico/seguro/confiable, horas "a las 7", "mañana")
- [X] T090 [US4] Ampliar `agent/nodes/parse_request.py` para texto libre: prompt JSON estricto `agent/prompts/parse.txt`, validación de la salida, resolución con el gazetteer y `clarification` (AMBIGUOUS_PLACE / OFF_TOPIC)
- [X] T091 [P] [US4] Implementar `agent/providers/gemini.py` (HTTP con httpx, timeout 6 s, clave `GEMINI_API_KEY`)
- [X] T092 [P] [US4] Implementar `agent/providers/groq.py` (HTTP con httpx, timeout 6 s, clave `GROQ_API_KEY`)
- [X] T093 [P] [US4] Crear `agent/providers/local.py` como stub documentado de `LocalProvider`
- [X] T094 [US4] Registrar `GeminiProvider` y `GroqProvider` en la fábrica `agent/providers/__init__.py` (creada en T029b, envueltos en `FallbackProvider`) y reportar el proveedor en `backend/app/api/health.py`
- [X] T095 [US4] Aceptar la variante `query` en `backend/app/api/recommendations.py` y mapear clarificaciones a 409/422 con mensajes en lenguaje sencillo
- [X] T096 [P] [US4] Implementar `frontend/src/components/AskBox.tsx` (campo de texto etiquetado "¿A dónde quieres ir?", compatible con dictado del teclado) y `frontend/src/components/DisambiguationDialog.tsx` (diálogo accesible con candidatos); integrarlos en `frontend/src/pages/Home.tsx`; sin conexión, aviso accesible y foco al formulario
- [X] T097 [US4] Implementar `frontend/src/components/LiveAnswer.tsx` (región `aria-live="polite"` que anuncia la explicación) e integrarlo en `frontend/src/pages/Results.tsx`
- [X] T098 [US4] Revisión de accesibilidad de todas las páginas en `frontend/src/pages/`: orden de foco, etiquetas, encabezados, zonas táctiles ≥ 44 px, sin errores de `eslint-plugin-jsx-a11y` — ✔ eslint jsx-a11y sin errores; la prueba manual con lector de pantalla va en T113

**Checkpoint**: Escenario F completado con lector de pantalla.

---

## Phase 7: User Story 5 - Ver el territorio en el mapa (Priority: P5)

**Goal**: completar el mapa iniciado en la Phase 2b (y la ruta dibujada en T059): incidentes activos y alternativa textual accesible.

**Independent Test**: tras el Escenario B, abrir el mapa y verificar alternativas e incidentes; repetir en modo avión.

- [X] T102 [US5] Mostrar en `frontend/src/pages/Map.tsx` los incidentes activos de `GET /api/reports` (categoría, confirmaciones) y ofrecer desde el mapa un enlace a la descripción textual (`RouteText`) como alternativa accesible

**Checkpoint**: mapa funcional en línea y offline.

---

## Phase 8: User Story 6 - Seguir funcionando si falla el servicio de IA (Priority: P6)

**Goal**: cualquier fallo del proveedor externo cae en `MockProvider` sin interrumpir el flujo.

**Independent Test**: Escenario E — clave inválida o sin red → recomendación normal con `explanation_provider: "mock"`.

- [X] T103 [P] [US6] Tests en `agent/tests/test_fallback.py`: timeout > 6 s, excepción, JSON inválido, cifras no validadas y clave ausente → Mock; `explanation_provider` correcto
- [X] T104 [US6] Propagar `explanation_provider` hasta la respuesta de `backend/app/api/recommendations.py` y cubrir en `agent/providers/fallback.py` (creado en T029b) el caso de explicación rechazada por el validador de cifras
- [X] T105 [US6] Test de integración del Escenario E en `backend/tests/integration/test_scenario_e.py` (`LLM_PROVIDER=gemini` con clave inválida)

**Checkpoint**: Escenario E en verde.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: despliegue robusto, verificación y preparación del pitch (Gates 8 y 9)

- [X] T106 [P] Crear `.github/workflows/keepalive.yml` (cron cada 10 min a `/api/health`, `workflow_dispatch`, desactivado fuera del evento)
- [X] T107 [P] Crear `frontend/lighthouserc.json` (categoría accessibility ≥ 0,9 en todas las rutas) y añadir el paso Lighthouse CI a `.github/workflows/ci.yml`
- [ ] T108 Re-medir memoria y arranque con `docker run -m 512m` durante los escenarios A–F con carga (pico ≤ 450 MB) y actualizar `docs/architecture/memory.md`; si se supera, seguir `docs/deploy/hf-spaces.md` — ⏸ requiere datos reales y carga en Render
- [X] T109 [P] Documentar el despliegue en `docs/deploy/render.md` (servicio, imagen GHCR, variables, secreto `RENDER_DEPLOY_HOOK`) y el respaldo en `docs/deploy/hf-spaces.md`
- [X] T110 [P] Completar `README.md` con prerrequisitos, ETL, ejecución local, pruebas y despliegue (enlazando `specs/001-muevete-cb-mvp/quickstart.md`)
- [ ] T111 [P] Confirmar tarifas vigentes y regla de transbordo en `backend/config/fares.yaml` (P-06) — ⏸ tarifas marcadas POR CONFIRMAR en `fares.yaml`
- [X] T112 [P] Redactar indicadores de impacto sin inventar resultados en `docs/pitch/indicators.md` (P-10) y guion de demo de 14 pasos en `docs/pitch/demo-script.md`
- [ ] T113 Ejecutar la validación manual de `specs/001-muevete-cb-mvp/quickstart.md` §6 (A–F, NL, demo completa) en 2 Android + 1 iPhone y registrar evidencia en `docs/pitch/validation.md` — ⏸ validación manual en teléfonos pendiente
- [ ] T114 Generar el QR de la URL de Render en `docs/pitch/qr.png`, activar `keepalive.yml`, congelar código y etiquetar `v1.0.0-demo` en `main` — ⏸ pendiente URL de Render para el QR y congelamiento

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup; **bloquea todas las historias**. T008 (datos reales) solo bloquea T015–T022 con datos reales; el resto avanza con la red de juguete (T038).
- **Paquete offline base (T022b)**: T035 (Dockerfile), T057 (autocompletado offline) y T100 (mapa) dependen de T022b; el nivel c (T079) solo lo necesita US3.
- **Mapa base (Phase 2b)**: depende de Foundational (T022b, T027); cierra el **Gate 2**, requisito para empezar US1.
- **US1 (Phase 3)**: depende de la Phase 2b (Gate 2); T059 reutiliza `MapView` y los estilos para dibujar la ruta.
- **US2 (Phase 4)**: depende de US1 (enchufa incidentes en el motor, T050 → T067; `MapView` para `LocationPicker`).
- **US3 (Phase 5)**: depende de US2 (el formulario de reporte y el modelo de reporte).
- **US4 (Phase 6)**: depende de US1 (grafo del agente y endpoint).
- **US5 (Phase 7)**: depende de la Phase 2b y de US2 (incidentes).
- **US6 (Phase 8)**: depende solo de US1 (`FallbackProvider` ya existe desde T029b).
- **Polish (Phase 9)**: tras las historias deseadas.

### Story Order

```text
Setup → Foundational (Gate 1) → Mapa base 2b (Gate 2) → US1 (Gate 3) ─┬─► US2 ─┬─► US3
                                                                       │        └─► US5 (resto)
                                                                       ├─► US4
                                                                       └─► US6
```

### Within Each User Story

- Tests listados primero; modelos → servicios → endpoints → UI → integración.
- El test de integración del escenario cierra la historia.

### Parallel Opportunities

- Setup: T003–T009 en paralelo.
- Foundational: T015, T016, T018 en paralelo; T025, T029, T030, T031, T033, T036 en paralelo con el ETL.
- Phase 2b: T099 (Backend) y T101 (Frontend) en paralelo en cuanto existe T022b, mientras Arquitectura cierra T035–T038b.
- Durante US1: T054 (rutas comunitarias, GIS) en paralelo con el motor; UI (T057, T058) en paralelo con el backend.
- Tras US1: **US2** (Backend + Frontend: T071–T073 en paralelo con su backend), **US4** (Arquitectura) y **US6** en paralelo.

---

## Parallel Example: User Story 1

```bash
# Tests primero (en paralelo):
Task: "T039 Tests del motor en backend/tests/unit/test_route_engine.py"
Task: "T040 Tests de scoring en backend/tests/unit/test_scoring.py"
Task: "T041 Test del validador en agent/tests/test_explain_validator.py"
Task: "T042 Contrato de /api/recommendations en backend/tests/contract/test_recommendations_contract.py"

# Modelos, gazetteer, datos y UI en paralelo:
Task: "T043 Modelos en backend/app/models/recommendation.py"
Task: "T044 Gazetteer en backend/app/services/gazetteer.py"
Task: "T054 Rutas comunitarias simuladas en data/seed/community_routes.geojson"
Task: "T057 Página Inicio en frontend/src/pages/Home.tsx"
Task: "T058 Resultados en frontend/src/pages/Results.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "T061 Reglas de reportes en backend/tests/unit/test_report_rules.py"
Task: "T064 Modelos en backend/app/models/report.py"
Task: "T066 Fotos en backend/app/services/photos.py"
Task: "T071 IndexedDB en frontend/src/offline/db.ts"
Task: "T072 Compresión de fotos en frontend/src/offline/photo.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2 → Gate 1 (PWA abre en Render, RAM medida).
2. Phase 2b → Gate 2 (mapa y datos cargan, también en modo avión).
3. Phase 3 (US1) → **STOP and VALIDATE** con el Escenario A y su ruta en el mapa → Gate 3.
4. Deploy (push a `main`).

### Incremental Delivery (alineado con los bloques del plan de batalla)

| Bloque | Fases | Gate |
|---|---|---|
| 0–1 Arranque, datos y esqueleto | 1, 2, 2b | 1, 2 |
| 2 Ruta funcional | 3 (US1) | 3 |
| 3 Reportes | 4 (US2) | 4, 5 |
| 4 Offline | 5 (US3) | 6, 7 |
| 5 Integración | 6 (US4), 7 (US5), 8 (US6) | — |
| 6 Deploy + ensayo | 9 | 8, 9 |

### Parallel Team Strategy (4 personas)

- **Backend**: T010–T028, T099 (bloque 1), motor US1 (T043–T053, T060), reportes US2 (T064–T070, T075), sync US3 (T078), T079 nivel c.
- **Frontend**: T031–T034, T100–T101 (bloque 1, con GIS), UI US1 (T057–T059), US2 (T071–T074), US3 (T080–T086), US5 (T102), US4 UI (T096–T098).
- **GIS**: T008, T014–T022 y T022b con Backend, estilos y capas de T100–T101 con Frontend, T054, T056, T111–T112.
- **Arquitectura**: T001–T002, T029–T030 (incl. T029b), T035–T038b, agente US1 (T051–T052), US4 (T087–T095), US6 (T103–T105), T106–T109, T114.

Regla de la constitución: si un gate falla, **no** se inicia ninguna tarea de una fase posterior.

---

## Notes

- [P] = archivos distintos y sin dependencias pendientes.
- Cada historia es demostrable al cerrar su checkpoint.
- Commit por tarea o grupo lógico en `feature/*` → PR a `dev` → PR a `main`.
- Evitar: tareas vagas, dos tareas sobre el mismo archivo en paralelo, reabrir decisiones de la constitución sin bloqueo real.
