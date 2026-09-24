# data/raw — archivos originales (P-03 / P-04)

Colocar aquí los archivos **sin modificar**. Los > 50 MB van con Git LFS (`.gitattributes`).
El ETL (`python -m backend.etl.build`) los lee según `backend/etl/sources.yaml`; si los nombres de
archivo o de atributos reales difieren, **ajustar `sources.yaml`**, no el código.

| Archivo esperado | Contenido | Atributos requeridos (nombre configurable) | CRS |
|---|---|---|---|
| `BarriosCatastrales.geojson` | Polígonos de barrios | `CODIGO_BARRIO`, `NOMBRE_BARRIO`, `LOCALIDAD` | WGS84 (si no, se reproyecta con pyproj) |
| `TrazadoTroncal.geojson` | Líneas troncales TM | `CODIGO_TRONCAL`, `NOMBRE_TRONCAL` | WGS84 |
| `RutasProvisionales.geojson` | Líneas de rutas provisionales | `CODIGO_RUTA` (= `route_short_name` del GTFS), `NOMBRE_RUTA` | WGS84 |
| `ParaderosZonalesSITP.geojson` | Puntos de paraderos | `CODIGO_PARADERO`, `NOMBRE_PARADERO` | WGS84 |
| `EstacionesTransmilenio.geojson` | Puntos de estaciones (troncal y TransMiCable) | `CODIGO_ESTACION`, `NOMBRE_ESTACION`, `TIPO` (contiene "cable" para TransMiCable) | WGS84 |
| `MallaVialIntegrada.geojson` | Líneas de vías | `CODIGO_VIA`, `NOMBRE_VIA`, `JERARQUIA` (valores principales en `main_values`) | WGS84 |
| `gtfs_bogota.zip` | GTFS completo | `stops`, `routes`, `trips`, `stop_times`; opcionales `frequencies`, `shapes` | — |

## Mientras no estén los archivos reales

```bash
python -m backend.etl.build --mock --offline frontend/public/offline
```

Genera datos **SIMULADOS** en `data/raw/mock/` (ignorado por git) con el mismo formato. Todas las
fuentes quedan marcadas `(MOCK)` y la API informa `data_mode: "mock"`.

## Con los archivos reales

```bash
python -m backend.etl.build --raw data/raw --offline frontend/public/offline
```

Si falta un archivo o un atributo, el ETL termina con un mensaje que indica cuál y qué atributos
tiene el archivo, para ajustar `sources.yaml`.
