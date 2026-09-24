# Memoria y arranque (T038b / T108, P-05)

Presupuesto (research R-05): **≤ 300 MB RSS en reposo, ≤ 450 MB en pico**, arranque ≤ 20 s.

| Fecha | Datos | Entorno | Arranque | RSS reposo | RSS pico (30 consultas) | Resultado |
|---|---|---|---|---|---|---|
| 2026-09-24 | MOCK (25 paradas, 18 patrones) | Windows, Python 3.13, proceso local (psutil) | 9,2 s | 92 MB | 92 MB | ✅ dentro del presupuesto |
| _pendiente_ | REAL (GTFS Bogotá completo) | `docker run -m 512m` | | | | Medir al cargar los datos reales |

**Nota:** con datos mock casi toda la memoria son librerías (FastAPI, LangGraph, Shapely). El
riesgo real está en el grafo del GTFS completo: repetir la medición con
`docker build --build-arg DATA_MODE=real` y `docker run -m 512m` en cuanto estén los archivos en
`data/raw/`. Si RSS > 300 MB en reposo, activar el plan B (`docs/deploy/hf-spaces.md`).
