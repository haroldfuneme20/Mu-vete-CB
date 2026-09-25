# data/raw — archivos originales (P-03 / P-04)

Archivos **sin modificar**. El ETL (`python -m backend.etl.build`) los lee según
`backend/etl/sources.yaml`; si cambian nombres de archivo o de atributos, **ajustar
`sources.yaml`**, no el código. Revisión de los datos: 2026-09-24.

| Archivo | Contenido | Uso en el sistema | Atributos usados |
|---|---|---|---|
| `Sector_CB.geojson` | 165 sectores catastrales (Ciudad Bolívar, Usme, Tunjuelito, Bosa, Puente Aranda) | Barrios de origen/destino y validación de Ciudad Bolívar | `SCACODIGO`, `SCANOMBRE`, `LocNombre` |
| `EstacionesTrasmiCB.geojson` | 34 estaciones troncales | Estaciones (fusionadas con el GTFS a ≤ 80 m) | `num_est`, `nom_est` |
| `Estaciones_cable.geojson` | 4 estaciones TransMiCable | Estaciones de cable | `cod_nodo`, `nom_est` |
| `ParaderosSITP_CB.geojson` | 672 paraderos zonales | Paraderos (fusionados con el GTFS a ≤ 15 m) | `cenefa`, `nombre_par` |
| `TrazadoTroncal_CB.geojson` | 5 trazados troncales | Mapa (nivel b offline) | `id_trazado`, `nom_traz` |
| `RutasProvisional_lnformales.geojson` | 87 rutas **provisionales SITP oficiales** (`RSPTRUTA=PROVISIONAL`) | Solo mapa (no están en el GTFS) | `RSPCDEFINI`, `RSPDENOMIN` |
| `MallaVial_CB.geojson` | 17.556 tramos viales | Vías principales del mapa offline (`AK`, `AC`) | `MVICODIGO`, `MVIETIQUET`, `MVITIPO` |
| `GTFS_20260818.zip` | GTFS TransMilenio S.A. de toda Bogotá (8.328 paradas, 1.030 rutas, 180.571 viajes) | Motor de rutas: patrones, tiempos, frecuencias, transbordos, tarifa | agencias → modo; día hábil (`service_day: monday`) |
| `CableAereo_CB.geojson` | Cables del POT (Decreto 555), en su mayoría **proyectados** | **Excluido**: no son servicios operativos | — |
| `Rutas_SITP.geojson` | Trazados de rutas SITP | **No usado**: los recorridos ya vienen en el GTFS | — |

## El GTFS no va en git

Pesa 112 MB (> 100 MB, límite de GitHub) y está en `.gitignore`. Publicarlo como **asset de un
Release** del repositorio y pasar su URL al build:

- Render (build directo del Dockerfile): variable de entorno `GTFS_URL=<url del asset>`.
- GitHub Actions (`deploy.yml`): variable de repositorio `GTFS_RELEASE_URL`.

## Comandos

```bash
python -m backend.etl.build --raw data/raw --offline frontend/public/offline   # datos reales
python -m backend.etl.build --mock --offline frontend/public/offline           # datos simulados
```
