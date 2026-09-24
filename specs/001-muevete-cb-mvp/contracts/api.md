# Contrato REST: Muévete CB API

Base: mismo dominio que la PWA (`/api/*`). JSON UTF-8. Sin autenticación (FR-034).
Errores con forma común:

```json
{ "error": { "code": "OUT_OF_COVERAGE", "message": "Texto en lenguaje sencillo", "details": {} } }
```

Códigos: `VALIDATION_ERROR` (422), `OUT_OF_COVERAGE` (422), `SAME_ORIGIN_DESTINATION` (422),
`AMBIGUOUS_PLACE` (409, con `details.candidates`), `NO_ROUTE` (404), `PAYLOAD_TOO_LARGE`
(413), `INTERNAL` (500).

---

## GET `/api/health`

```json
{ "status": "ok", "data_version": "2026-09-24T08:00:00Z", "llm_provider": "mock",
  "reports_active": 3, "uptime_s": 1234 }
```

`status` = `ok` solo si la base y el grafo están cargados (FR-032).

## GET `/api/places?q=paraiso&limit=5`

Búsqueda en el gazetteer (autocompletar del formulario).

```json
{ "items": [
  { "ref_id": "b_1234", "kind": "barrio", "display_name": "Paraíso",
    "localidad": "Ciudad Bolívar", "lat": 4.5, "lng": -74.1 } ] }
```

## GET `/api/stops?bbox=minLng,minLat,maxLng,maxLat&kind=tm_station`

Paradas en una caja (mapa). Máx. 2 000 por respuesta. Cada item: `id`, `name`, `kind`,
`lat`, `lng`, `source_kind`.

## GET `/api/routes` · GET `/api/routes/{id}`

Lista paginada (`?mode=community&page=1`) y detalle de un patrón: `id`, `name`, `mode`,
`stops[]`, `service_start`, `service_end`, `headway_min`, `fare`, `source_kind`,
`confidence`, `last_updated`, `geometry` (GeoJSON, solo en detalle).

## POST `/api/recommendations`

Entrada estructurada (formulario) **o** texto libre (lenguaje natural). Exactamente uno de
`query` o (`origin` + `destination`).

```json
{
  "origin": { "ref_id": "b_1234" },
  "destination": { "lat": 4.6019, "lng": -74.0721 },
  "priority": "fast",
  "depart_at": "2026-09-24T07:30:00-05:00"
}
```

```json
{ "query": "Necesito ir del barrio Paraíso al Portal Tunal, lo más confiable" }
```

`origin`/`destination`: `{ "ref_id" }` (gazetteer) o `{ "lat", "lng" }`.
`priority`: `balanced` (defecto) \| `fast` \| `cheap` \| `reliable`. `depart_at` opcional
(defecto: ahora).

**200**:

```json
{
  "request": {
    "origin": { "display_name": "Mirador del Paraíso", "localidad": "Ciudad Bolívar" },
    "destination": { "display_name": "Av. Jiménez", "localidad": "Santa Fe" },
    "priority": "fast", "depart_at": "2026-09-24T07:30:00-05:00",
    "interpreted_from_text": false
  },
  "recommended": {
    "id": "alt_9f2c", "rank": 1, "total_time_min": 62, "cost": 3200, "transfers": 1,
    "availability": 0.9, "reliability": 0.85, "confidence": 0.87, "score": 0.81,
    "legs": [
      { "mode": "transmicable", "route_name": "TransMiCable", "from_stop": "Mirador del Paraíso",
        "to_stop": "Portal Tunal", "stops": ["Mirador del Paraíso", "Manitas", "Juan Pablo II", "Portal Tunal"],
        "duration_min": 14, "wait_min": 1, "cost": 3200, "source_kind": "institutional",
        "confidence": 0.95, "last_updated": "2026-08-01", "reports": [],
        "geometry": { "type": "LineString", "coordinates": [[-74.1, 4.5]] } }
    ],
    "text_description": "Toma el TransMiCable en Mirador del Paraíso hasta Portal Tunal (4 paradas, 14 minutos)…",
    "evidence": [
      { "kind": "source", "label": "GTFS Bogotá", "source_id": "src_gtfs_bogota", "date": "2026-08-01" }
    ]
  },
  "alternatives": [ { "id": "alt_31aa", "rank": 2, "...": "misma forma" } ],
  "explanation": "Te recomiendo el TransMiCable y luego la troncal Caracas porque es la opción más rápida (62 minutos)…",
  "explanation_provider": "mock",
  "warning": null,
  "confidence": 0.87,
  "evidence": [ { "kind": "report", "label": "2 personas reportaron un bloqueo en la ruta comunitaria C1", "report_ids": ["…"] } ],
  "computed_at": "2026-09-24T07:30:01-05:00",
  "data_version": "2026-09-24T08:00:00Z"
}
```

Reglas del contrato:
- Mismas entradas + mismo `data_version` + mismos reportes vigentes → mismo `recommended.id`
  y mismo orden (FR-003, SC-003).
- `warning`: `null` \| `"all_affected"` (todas las alternativas viables tienen penalización por
  reportes). Si todas quedan invalidadas → **404** `NO_ROUTE` con sugerencia de otra hora o
  prioridad.
- Todo `leg` trae `source_kind`; si es `demo_simulated`, la UI muestra "simulada para la demo".
- `explanation` solo contiene cifras presentes en `recommended`/`alternatives` (validado en
  servidor; FR-007).
- Texto libre ambiguo → **409** `AMBIGUOUS_PLACE` con candidatos; fuera de tema → **422**
  `VALIDATION_ERROR` con `details.reason = "off_topic"` y mensaje amable (FR-009).

## POST `/api/reports`

`multipart/form-data`: campo `report` (JSON) + `photo` opcional (`image/jpeg`, ≤ 1 MB).

```json
{ "id": "3f1c…uuid", "anon_id": "a9…uuid", "category": "blockage",
  "location": { "lat": 4.5, "lng": -74.1 }, "description": "Vía cerrada",
  "created_at": "2026-09-24T07:40:00-05:00" }
```

**201** (nuevo) / **200** (ya existía, idempotente):

```json
{ "id": "3f1c…", "status": "accepted", "received_at": "…", "expires_at": "…",
  "affected_segments": 2, "confirmations": 1 }
```

`status`: `accepted` \| `duplicate`.

## POST `/api/sync`

Lote de hasta 20 reportes del outbox. `multipart/form-data`: `reports` (JSON array con la
forma de `/api/reports`) + archivos `photo_<id>` opcionales.

**200**:

```json
{ "results": [
    { "id": "3f1c…", "status": "accepted" },
    { "id": "77ab…", "status": "duplicate" },
    { "id": "90cd…", "status": "rejected", "error": { "code": "VALIDATION_ERROR", "message": "…" } } ],
  "server_time": "…", "recalculate": true }
```

El cliente marca `synced` los `accepted`/`duplicate`, deja `error` los `rejected` y, si
`recalculate`, vuelve a pedir la última recomendación (FR-023).

## GET `/api/reports?active=true&bbox=…`

Reportes para el mapa: `id`, `category`, `lat`, `lng`, `received_at`, `expires_at`,
`confirmations`, `has_photo`. Nunca expone `anon_id`.

## GET `/api/reports/{id}/photo`

`image/jpeg`. 404 si no hay foto.

---

## Recursos estáticos

- `/` → PWA (app shell).
- `/offline/manifest.json` → versión y lista de archivos del paquete offline (ver
  [offline-package.md](./offline-package.md)).
