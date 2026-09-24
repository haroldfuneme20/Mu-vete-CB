# Research: Muévete CB — MVP

**Feature**: `001-muevete-cb-mvp` | **Date**: 2026-09-24 | **Plan**: [plan.md](./plan.md)

Cada decisión sigue el formato Decision / Rationale / Alternatives considered. Las decisiones ya
fijadas por la constitución (v2.2.2) no se reabren; aquí solo se concretan.

---

## R-01. Algoritmo del motor de rutas sobre el GTFS de toda Bogotá

- **Decision**: RAPTOR simplificado **basado en frecuencias** con máximo 3 rondas (= 2
  transbordos). La red se modela como *patrones de viaje* (ruta + secuencia ordenada de
  paradas) con tiempo medio entre paradas consecutivas y *headway* (intervalo) por franja
  horaria. La espera se estima como la mitad del headway. Los transbordos a pie se precalculan
  entre paradas a ≤ 250 m. Cada ronda guarda el mejor tiempo por parada y el "padre" para
  reconstruir el camino; al final se extraen hasta K=10 candidatos distintos (por combinación
  de patrones), se aplican incidentes y el score, y se devuelven los 3 mejores.
- **Rationale**: es determinístico, acota los transbordos de forma natural (constitución VII:
  ≤ 2), no depende de horarios exactos de cada viaje (en Bogotá el SITP opera por frecuencia) y
  en una red de ~8 000 paradas y ~2 000 patrones responde en decenas de milisegundos en
  Python puro. Es un algoritmo de libro y fácil de explicar.
- **Alternatives considered**:
  - *Dijkstra/A\* sobre grafo tiempo-expandido*: grafo enorme con `stop_times` completos; no
    cabe en 512 MB y es excesivo.
  - *OpenTripPlanner / r5*: planificador multimodal completo (fuera de alcance por
    constitución I) y requiere JVM con varios GB de RAM.
  - *Rutas precalculadas solo para los escenarios*: rompe FR-002 (origen/destino libres).

## R-02. Preprocesamiento (ETL) y cuándo se construye la base

- **Decision**: el paquete `backend/etl/` construye `muevete.db` (SQLite) desde `data/raw/` **durante el
  build de la imagen Docker en GitHub Actions** (etapa separada con dependencias pesadas:
  pandas, pyogrio/shapely, pyproj, más las dependencias del backend porque el nivel c del paquete
  offline usa el motor). El ETL corre **antes** del build del frontend para que el paquete
  offline entre en el precache del Service Worker (orden: ETL → build PWA → runtime). La imagen final solo contiene la base ya construida y los
  datos semilla. Al arrancar, el servicio copia `muevete.db` a un archivo de trabajo y aplica
  los reportes semilla → cumple "reconstruir en cada arranque" sin gastar RAM/tiempo del plan
  gratuito. El mismo comando se ejecuta en local.
- **Rationale**: la RAM de Render (512 MB) se reserva para servir; el runner de Actions tiene
  7 GB. El resultado es reproducible (constitución IV, FR-030).
- **Alternatives considered**: construir al arrancar en Render (lento, riesgo de OOM);
  commitear la base generada (no reproducible, archivo binario grande en git).

## R-03. Almacenamiento de los archivos crudos en GitHub

- **Decision**: `data/raw/` versionado en el repo; archivos > 50 MB (probablemente el GTFS y la
  malla vial) con **Git LFS**. Si el GTFS supera la cuota gratuita de LFS (1 GB de ancho de
  banda/mes), se publica como *asset* de un GitHub Release y el workflow lo descarga por URL.
- **Rationale**: GitHub rechaza archivos > 100 MB y advierte desde 50 MB.
- **Alternatives considered**: descargar el GTFS del portal oficial en cada build (dependencia
  externa frágil en plena demo; la URL puede cambiar).

## R-04. SQLite con búsquedas espaciales sin SpatiaLite

- **Decision**: `sqlite3` de la librería estándar de Python con tablas virtuales **R\*Tree**
  (bounding boxes) + **Shapely 2** para la geometría fina (distancias, point-in-polygon de
  barrios, cercanía de reportes a segmentos). Geometrías guardadas como WKB. Coordenadas en
  WGS84; las distancias se calculan en metros con una proyección local (EPSG:3116 MAGNA-SIRGAS
  Bogotá) aplicada en el ETL. Al arrancar se verifica que el módulo R\*Tree está disponible
  (`PRAGMA compile_options` / crear una tabla rtree de prueba) y se falla con un mensaje claro
  si no.
- **Rationale**: constitución (SQLite, sin SpatiaLite). Las imágenes `python:3.12-slim` traen
  SQLite con RTREE habilitado.
- **Alternatives considered**: SpatiaLite (extensión nativa frágil); PostGIS (segundo servicio).

## R-05. Grafo en memoria y presupuesto de RAM

- **Decision**: al arrancar se cargan en memoria solo los arreglos compactos del motor
  (patrones, paradas de cada patrón con tiempos acumulados, transbordos a pie, headways) en
  estructuras de Python/`array`; geometrías y barrios se consultan en SQLite bajo demanda.
  Presupuesto: ≤ 300 MB de RSS en reposo, ≤ 450 MB en pico. Se mide con `docker stats` (P-05).
- **Rationale**: deja margen dentro de 512 MB para FastAPI, LangGraph y picos de consultas.
- **Alternatives considered**: cargar GeoDataFrames completos (varios cientos de MB).
- **Plan B**: si se supera el presupuesto, la misma imagen va a Hugging Face Spaces
  (constitución, contingencia).

## R-06. Resolución de lugares (gazetteer) y prevención de lugares inventados

- **Decision**: un *gazetteer* en SQLite con nombres normalizados (minúsculas, sin tildes, sin
  prefijos como "barrio"/"estación") de barrios catastrales, estaciones TransMilenio/
  TransMiCable, paraderos SITP y un pequeño listado de hitos (p. ej. "Av. Jiménez", "centro").
  La coincidencia usa `difflib`/`rapidfuzz` con umbral; varias coincidencias → se pide elegir.
  **El LLM solo extrae el texto de origen/destino; la resolución siempre la hace el
  gazetteer.**
- **Rationale**: FR-009 y constitución II (la IA no inventa lugares ni rutas).
- **Alternatives considered**: geocodificador externo (dependencia de red y cuota); dejar que
  el LLM devuelva coordenadas (riesgo de alucinación).

## R-07. LangGraph y proveedores LLM

- **Decision**: grafo de 4 nodos en `agent/` (`parse_request → retrieve_mobility_data →
  evaluate_routes → explain_result`) ejecutado en el mismo proceso del backend.
  `LLMProvider.generate(prompt) -> str` con `MockProvider` (por defecto), `GeminiProvider` y
  `GroqProvider` implementados con `httpx` directo contra sus APIs REST (sin SDKs pesados);
  `LocalProvider` queda como stub documentado. Selección por variable de entorno
  `LLM_PROVIDER`; si falta la clave o la llamada falla/excede 6 s, se usa `MockProvider`.
  - `parse_request`: la entrada de formulario salta el LLM (ya es estructurada); el texto libre
    va al LLM con salida JSON estricta; `MockProvider` usa reglas (palabras clave de prioridad:
    "rápido", "barato/económico", "seguro/confiable"; patrones "de X a Y", "desde X hasta Y").
  - `explain_result`: el LLM recibe **solo** los hechos calculados; un validador comprueba que
    cada número de la respuesta (minutos, pesos, %) exista en los hechos; si no, se descarta y
    se usa la plantilla determinística de `MockProvider`.
- **Rationale**: constitución II y V; FR-007, FR-031; SC-009.
- **Alternatives considered**: SDKs oficiales (más peso y dependencias); llamar al LLM también
  para el ranking (prohibido).

## R-08. PWA, caché offline y mapa

- **Decision**: React + Vite + `vite-plugin-pwa` (Workbox). *Precache* del app shell y del
  paquete offline (GeoJSON estáticos generados por el ETL, servidos desde `/offline/`).
  Presupuesto del paquete offline: ≤ 5 MB comprimido en total. Mapa con Leaflet
  (`react-leaflet`); fondo de mapa OSM solo con conexión (caché en tiempo de ejecución
  limitado a las teselas ya vistas, sin descarga masiva, respetando la política de uso de OSM);
  sin conexión el mapa muestra solo capas vectoriales sobre fondo neutro (FR-026).
  Librería de componentes: **MUI** (Material UI), por su soporte de accesibilidad y porque el
  mock la usa.
- **Rationale**: constitución III; mock.jpg.
- **Alternatives considered**: MapLibre con teselas vectoriales offline (paquete pesado,
  tiempo de preparación alto); Mapbox (requiere clave).

## R-09. Almacenamiento local, outbox y sincronización idempotente

- **Decision**: IndexedDB con la librería `idb`. Almacenes: `outbox` (reportes con su foto como
  Blob), `results` (últimas consultas y escenarios de demo), `meta` (`anon_id`,
  `last_sync_at`). Cada reporte lleva un `id` UUID generado en el cliente; el servidor hace
  *upsert* por `id`, así que reintentos no duplican. Sincronización: botón "Sincronizar ahora"
  + evento `online` + Background Sync solo donde exista (Chromium). `POST /sync` en lotes de
  hasta 20 reportes; la respuesta indica el estado por reporte.
- **Rationale**: FR-021, FR-022, SC-006; Safari no soporta Background Sync.
- **Alternatives considered**: `localStorage` (no admite Blobs y es síncrono); sincronización
  solo automática (no fiable en iOS).

## R-10. Fotos de reportes

- **Decision**: al adjuntar, se dibuja la imagen en un `canvas` con lado mayor ≤ 1280 px y se
  re-codifica a JPEG calidad 0,7 (lo que elimina todos los metadatos EXIF, incluido el GPS);
  si aún supera 1 MB se baja la calidad hasta 0,5 y, si persiste, se rechaza con mensaje. En el
  servidor se re-valida tamaño/tipo y se guarda en disco efímero (`/tmp/photos`).
- **Rationale**: constitución VI; FR-016.
- **Alternatives considered**: eliminar EXIF con una librería de parseo (más código, mismo
  resultado).

## R-11. Asociación reporte → tramo y regla de confirmación

- **Decision**: el ETL guarda la geometría de cada *segmento* (par de paradas consecutivas de
  un patrón) con índice R\*Tree. Un reporte se asocia a los segmentos a ≤ 100 m. Un reporte
  aplica penalización parcial; ≥ 2 reportes con misma categoría, mismo segmento, vigentes (2 h
  desde `received_at` del servidor) y `anon_id` distintos escalan (bloqueo → segmento
  inválido). Todos los parámetros viven en `backend/config/engine.yaml`.
- **Rationale**: FR-017, FR-018, clarificación Q3; edge case de reloj desfasado.

## R-12. Accesibilidad verificable

- **Decision**: MUI + HTML semántico; región `aria-live="polite"` para la respuesta del agente;
  descripción textual de cada alternativa (FR-012); tema con contraste AA y tipografía base
  16 px (`rem`). Verificación automática con **Lighthouse CI** en GitHub Actions (umbral 90) y
  `eslint-plugin-jsx-a11y`; verificación manual con TalkBack y VoiceOver (SC-007).
- **Rationale**: constitución VIII.

## R-13. Pruebas y CI/CD

- **Decision**:
  - Backend: `pytest` + `httpx`/`TestClient`. Tests unitarios del motor con una *red de
    juguete* fija (no dependen del GTFS real) + tests de contrato de la API + test de la regla
    de confirmación de reportes + test de reproducibilidad (misma consulta → mismo orden).
  - Frontend: `vitest` para la lógica de outbox y compresión de fotos; Lighthouse CI.
  - Lint: `ruff` (Python) y `eslint` (TS).
  - Workflows: `ci.yml` (PR → lint, tests, build), `deploy.yml` (push a `main` → build imagen
    multi-etapa → GHCR → deploy hook de Render), `keepalive.yml` (cron cada 10 min hacia
    `/health`, activado solo durante el evento).
- **Rationale**: constitución (CI/CD, gates, tests del motor).

## R-14. Tarifas y costo

- **Decision**: tarifas en `backend/config/fares.yaml` (valor TransMilenio/TransMiCable, valor
  SITP zonal, regla de transbordo integrado, tarifa declarada por ruta comunitaria). Valores
  iniciales marcados como *por confirmar* (P-06); el motor no tiene tarifas en el código.
- **Rationale**: los valores cambian cada año; se mantienen fuera del código.

## R-15. Rendimiento de arranque en frío (Render)

- **Decision**: la PWA muestra un estado "Despertando el servicio…" si `/health` tarda > 2 s;
  `keepalive.yml` evita el sueño durante el evento. Tiempo objetivo de arranque del contenedor
  ≤ 20 s (copiar base + cargar grafo).
- **Rationale**: edge case "servidor dormido"; SC-002.

---

## Resumen de NEEDS CLARIFICATION

No quedan incógnitas técnicas bloqueantes. Los valores que dependen de datos reales se
mantienen como **pendientes de datos** (no de diseño) y están en `spec.md`:
P-02a, P-03, P-04, P-05, P-06, P-07, P-08, P-09, P-10, P-12, P-13.
