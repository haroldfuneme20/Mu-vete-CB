# Memoria y arranque (T038b / T108, P-05)

Presupuesto (research R-05): **≤ 300 MB RSS en reposo, ≤ 450 MB en pico**, arranque ≤ 20 s.

| Fecha | Datos | Entorno | Arranque | RSS reposo | RSS pico | Consulta (Escenario A) | Resultado |
|---|---|---|---|---|---|---|---|
| 2026-09-24 | MOCK (25 paradas, 18 patrones) | Windows, Python 3.13, proceso local (psutil) | 9,2 s | 92 MB | 92 MB | < 0,2 s | ✅ |
| 2026-09-24 | REAL (8.421 paradas, 939 patrones GTFS + 6 comunitarios, 48.693 tramos, 54.470 transbordos) | Windows, Python 3.13, proceso local (psutil) | < 1 s (carga del grafo) | 120 MB | 127 MB | mediana 1,9 s, máx. 2,6 s | ✅ |
| _pendiente_ | REAL | `docker run -m 512m` en Render | | | | | Confirmar en el contenedor |

- ETL con datos reales: ~2,5–3 min y ~120 MB de RAM (stop_times en una base SQLite temporal).
- La consulta tarda ~2 s porque el motor repite RAPTOR hasta `k_search = 10` veces para dar
  alternativas distintas; si hiciera falta bajarla, reducir `candidates.k_search` en
  `engine.yaml` (p. ej. a 6).
- Si en Render el RSS supera 300 MB en reposo, activar el plan B (`docs/deploy/hf-spaces.md`).
