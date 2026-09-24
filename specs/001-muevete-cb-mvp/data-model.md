# Data Model: Muévete CB — MVP

**Feature**: `001-muevete-cb-mvp` | **Date**: 2026-09-24 | **Plan**: [plan.md](./plan.md)

Tres capas de datos: (1) base SQLite del servidor, generada por el ETL; (2) configuración del
motor; (3) almacenamiento local del teléfono (IndexedDB). Coordenadas en WGS84 (lat/lng);
geometrías como WKB; distancias en metros; tiempos en segundos internamente y en minutos en la
API.

---

## 1. Base del servidor (`muevete.db`)

### `sources` — Fuente de datos

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT PK | p. ej. `src_gtfs_bogota` |
| `name` | TEXT | nombre legible |
| `file` | TEXT | archivo original en `data/raw/` |
| `kind` | TEXT | `institutional` \| `community` \| `territorial` \| `demo_simulated` |
| `published_at` | TEXT (ISO date) | fecha de la fuente |
| `loaded_at` | TEXT (ISO datetime) | fecha del ETL |

Toda fila de `stops`, `patterns` y `barrios` referencia un `source_id` (constitución IV).

### `barrios` — Barrio catastral

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT PK | id original del archivo |
| `name` | TEXT | |
| `localidad` | TEXT | valor del atributo de localidad (P-04 confirma el nombre real del campo) |
| `is_ciudad_bolivar` | INTEGER (0/1) | `localidad` normalizada = "ciudad bolivar" |
| `centroid_lat`, `centroid_lng` | REAL | punto de referencia para origen/destino |
| `geom` | BLOB (WKB) | polígono |
| `source_id` | TEXT FK | `territorial` |

Índice `barrios_rtree` (R\*Tree por bbox) para point-in-polygon.

### `stops` — Parada / Estación

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT PK | `stop_id` GTFS o id del archivo de paraderos/estaciones |
| `name` | TEXT | |
| `kind` | TEXT | `sitp_zonal` \| `tm_station` \| `transmicable` \| `community_point` |
| `lat`, `lng` | REAL | |
| `barrio_id` | TEXT FK NULL | barrio que la contiene |
| `source_id` | TEXT FK | |
| `source_ref` | TEXT | id original en el archivo fuente (trazabilidad) |

Índice `stops_rtree`. Paradas duplicadas entre GTFS y archivos de paraderos se fusionan por
cercanía (≤ 15 m) y nombre similar; se conserva la referencia a ambas fuentes.

### `patterns` — Patrón de viaje (ruta)

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT PK | |
| `route_ref` | TEXT | `route_id` GTFS o id de ruta comunitaria |
| `name` | TEXT | nombre público (p. ej. "TransMiCable", "Ruta zonal 17-4") |
| `mode` | TEXT | `troncal` \| `provisional` \| `zonal` \| `transmicable` \| `community` |
| `fare_class` | TEXT | clave en `fares.yaml` |
| `service_start`, `service_end` | TEXT (HH:MM) | horario |
| `headway_peak_s`, `headway_offpeak_s` | INTEGER | intervalo por franja |
| `reliability` | REAL 0–1 | confiabilidad operativa base |
| `confidence` | REAL 0–1 | confianza en el dato (comunitarias simuladas 0,5–0,6) |
| `last_updated` | TEXT ISO | |
| `source_id` | TEXT FK | |

### `pattern_stops` — Secuencia de paradas del patrón

| Campo | Tipo | Regla |
|---|---|---|
| `pattern_id` | TEXT FK | |
| `seq` | INTEGER | 0..n, PK compuesta con `pattern_id` |
| `stop_id` | TEXT FK | |
| `t_from_start_s` | INTEGER | tiempo acumulado desde la primera parada (mediana GTFS) |

### `segments` — Tramo entre paradas consecutivas

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT PK | `{pattern_id}:{seq}` |
| `pattern_id` | TEXT FK | |
| `seq` | INTEGER | tramo entre `seq` y `seq+1` |
| `geom` | BLOB (WKB) | línea (de `shapes.txt`, trazado troncal o malla vial) |

Índice `segments_rtree`. Se usa para asociar reportes (≤ 100 m).

### `footpaths` — Transbordo a pie

| Campo | Tipo | Regla |
|---|---|---|
| `from_stop_id`, `to_stop_id` | TEXT FK | PK compuesta |
| `walk_s` | INTEGER | distancia / velocidad a pie (≤ 250 m) |

### `gazetteer` — Nombres resolubles

| Campo | Tipo | Regla |
|---|---|---|
| `name_norm` | TEXT | minúsculas, sin tildes ni prefijos |
| `display_name` | TEXT | |
| `kind` | TEXT | `barrio` \| `station` \| `stop` \| `landmark` |
| `ref_id` | TEXT | id en su tabla |
| `lat`, `lng` | REAL | |
| `localidad` | TEXT | para desambiguar |

### `reports` — Reporte ciudadano

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT PK | UUID generado en el cliente (idempotencia) |
| `anon_id` | TEXT | UUID del dispositivo |
| `category` | TEXT | `blockage` \| `delay` \| `route_change` \| `risk` \| `other` |
| `lat`, `lng` | REAL | obligatorios; dentro de la caja de Bogotá |
| `description` | TEXT NULL | ≤ 280 caracteres |
| `photo_path` | TEXT NULL | archivo en `/tmp/photos`, JPEG ≤ 1 MB |
| `created_at` | TEXT ISO | hora del cliente (informativa) |
| `received_at` | TEXT ISO | hora del servidor (base de la vigencia) |
| `expires_at` | TEXT ISO | `received_at` + 2 h |
| `source` | TEXT | `citizen` \| `demo_simulated` (semilla) |

### `report_segments` — Asociación reporte ↔ tramo

| Campo | Tipo |
|---|---|
| `report_id` | TEXT FK |
| `segment_id` | TEXT FK |
| `distance_m` | REAL |

**Reglas derivadas (en tiempo de consulta)**: para cada `segment_id` y `category` se cuentan
los reportes vigentes con `anon_id` distintos → `n_confirm`. `n_confirm = 1` → penalización
parcial; `n_confirm ≥ 2` → escalada (bloqueo invalida). Ver `engine.yaml`.

---

## 2. Configuración (`backend/config/`)

### `engine.yaml`

```yaml
walk:
  max_access_m: 600
  speed_kmh: 4.5
  max_transfer_m: 250
transfers:
  max: 2
  penalty_s: 300
wait:
  headway_factor: 0.5
candidates:
  k_search: 10
  k_return: 3
reports:
  validity_h: 2
  radius_m: 100
  partial:            # 1 reporte
    blockage: { add_s: 900, reliability: -0.3 }
    delay:    { add_s: 600 }
    risk:     { reliability: -0.3 }
    route_change: { availability: -0.3 }
    other:    {}
  confirmed:          # >= 2 reportes de anon_id distintos
    blockage: { invalidate: true }
    multiplier: 2
  caps: { max_add_s: 1800, min_score_component: 0.1 }
weights:              # tiempo, disponibilidad, confiabilidad, costo
  balanced:  [0.40, 0.25, 0.20, 0.15]
  fast:      [0.55, 0.20, 0.15, 0.10]
  cheap:     [0.25, 0.20, 0.15, 0.40]
  reliable:  [0.25, 0.25, 0.40, 0.10]
tie_break: [time_asc, id_asc]
```

### `fares.yaml`

Valores por confirmar (P-06): `tm_troncal`, `transmicable`, `sitp_zonal`, regla
`integrated_transfer`, `community.<route_id>`.

---

## 3. Entidades de respuesta (no persistidas)

### `Leg` (tramo de una alternativa)

`mode`, `pattern_id`/`route_name` (NULL si es caminata), `from_stop`, `to_stop`,
`stops` (lista ordenada de nombres), `duration_min`, `wait_min`, `cost`, `source_kind`,
`confidence`, `last_updated`, `reports` (lista `{category, n_confirm, effect}`),
`geometry` (GeoJSON LineString).

### `Alternative`

`id` (hash determinístico de la secuencia de patrones), `legs[]`, `total_time_min`,
`cost`, `transfers`, `availability` (0–1), `reliability` (0–1), `confidence` (0–1),
`score` (0–1), `rank`, `text_description` (FR-012), `evidence[]`.

### `Recommendation`

`request` (origen, destino, prioridad, hora resueltos), `recommended` (`Alternative`),
`alternatives[]` (hasta 2 más), `explanation` (texto), `explanation_provider`
(`mock` \| `gemini` \| `groq`), `warning` (`null` \| `"all_affected"`), `confidence`, `evidence[]`, `computed_at`,
`data_version`.

### `Evidence`

`kind` (`source` \| `report` \| `schedule`), `label`, `source_id`/`report_ids`,
`date`.

---

## 4. Almacenamiento local (IndexedDB `muevete-cb`)

| Store | Clave | Contenido |
|---|---|---|
| `outbox` | `id` (UUID) | reporte completo + `photo` (Blob) + `sync_status` + `attempts` + `last_error` |
| `results` | `query_key` | última `Recommendation` por consulta + escenarios de demo precargados |
| `meta` | clave | `anon_id`, `last_sync_at`, `offline_package_version` |
| `prefs` | clave | preferencias locales de accesibilidad (tamaño de texto) — sin cuenta |

### Estados de un reporte (cliente)

```text
draft ──guardar──► pending_sync ──sincronizar──► syncing ──ok──► synced
                        ▲                            │
                        └────────── error ◄──────────┘ (reintento; attempts++)
```

- `synced` solo tras respuesta del servidor con `accepted` o `duplicate` para ese `id`.
- Un reporte en `syncing` interrumpido vuelve a `pending_sync` al reabrir la app.

---

## 5. Validaciones clave

| Regla | Origen |
|---|---|
| Origen o destino con `is_ciudad_bolivar = 1` | FR-002 |
| Origen ≠ destino (> 200 m) | Edge case |
| `priority ∈ {balanced, fast, cheap, reliable}` | FR-001 |
| `category` en el catálogo; `lat/lng` obligatorios | FR-014 |
| `description` ≤ 280 caracteres; foto JPEG ≤ 1 MB | FR-016 |
| `id` de reporte UUID; upsert idempotente | FR-022 |
| `source_kind` presente en todo `Leg` | FR-027, FR-028 |
