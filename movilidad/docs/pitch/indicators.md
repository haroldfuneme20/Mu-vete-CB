# Indicadores de impacto (T112, P-10)

Regla (constitución IV, riesgo R9): **no se inventan resultados**. Solo indicadores de proceso y
producto que el sistema puede medir hoy. Los valores se leen de la base (`muevete.db`) o de la API
el día de la demo.

| Dimensión | Indicador | Cómo se mide | Valor en demo |
|---|---|---|---|
| Cobertura | Rutas comunitarias digitalizadas | `patterns` con `mode = community` / 2 sentidos | _medir_ |
| Cobertura | Paradas y estaciones integradas | `count(*)` de `stops` | _medir_ |
| Actualización | % de rutas con fecha de actualización | `patterns.last_updated` no nulo | _medir_ |
| Actualización | Tiempo entre reporte y cambio de ranking | reporte → siguiente consulta (s) | _medir en ensayo_ |
| Participación | Reportes capturados | `count(*)` de `reports` (sin semillas) | _medir en ensayo_ |
| Participación | % de reportes capturados offline | outbox sincronizados / total | _medir en ensayo_ |
| Calidad | % de recomendaciones con evidencia | respuestas con `evidence` no vacío (hoy 100 % por diseño) | 100 % |
| Calidad | Confianza promedio de la recomendación | promedio de `confidence` en escenarios A–F | _medir_ |
| Operación | Tiempo de respuesta p95 | test `test_scenario_a.py::test_p95_under_5_seconds` | _medir en Render_ |
| Operación | % de sincronizaciones exitosas | resultados `accepted`/`duplicate` de `/api/sync` | _medir en ensayo_ |

Con datos mock estos valores **no** describen el territorio: solo demuestran que el sistema
puede medirlos. Recalcular con los datos reales antes del pitch.
