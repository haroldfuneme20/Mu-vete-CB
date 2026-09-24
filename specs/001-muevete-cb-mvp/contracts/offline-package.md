# Contrato del paquete offline

Generado por el ETL en `frontend/public/offline/` y precacheado por el Service Worker.
Presupuesto total ≤ 5 MB comprimido (gzip/brotli).

## `/offline/manifest.json`

```json
{
  "version": "2026-09-24T08:00:00Z",
  "files": [
    { "path": "cb_barrios.geojson",      "level": "a", "bytes": 0 },
    { "path": "cb_stops.geojson",        "level": "a", "bytes": 0 },
    { "path": "cb_roads_main.geojson",   "level": "a", "bytes": 0 },
    { "path": "community_routes.geojson","level": "a", "bytes": 0 },
    { "path": "tm_trunk.geojson",        "level": "b", "bytes": 0 },
    { "path": "tm_stations.geojson",     "level": "b", "bytes": 0 },
    { "path": "demo_scenarios.json",     "level": "c", "bytes": 0 },
    { "path": "places_index.json",       "level": "a", "bytes": 0 }
  ]
}
```

## Niveles (constitución III)

| Nivel | Contenido | Simplificación |
|---|---|---|
| a | Ciudad Bolívar: barrios, paraderos/estaciones, vías principales (malla vial filtrada por jerarquía), rutas comunitarias simuladas, índice de lugares para el formulario offline | tolerancia ~5 m, solo atributos `id`, `name`, `kind`, `source_kind` |
| b | Toda Bogotá: trazado troncal y estaciones TransMilenio/TransMiCable | tolerancia ~15 m |
| c | `Recommendation` precalculadas de los escenarios A y F (y sus variantes por prioridad) | JSON de la API |

Las "últimas consultas" de la persona no están en el paquete: se guardan en IndexedDB
(`results`) al recibir cada respuesta.

## Reglas

- Cada `Feature` lleva `properties.source_kind`; los `demo_simulated` se dibujan con estilo
  distinto y leyenda "simulada".
- Si `manifest.version` cambia, el Service Worker actualiza el paquete en segundo plano con
  conexión; nunca borra el `outbox`.
