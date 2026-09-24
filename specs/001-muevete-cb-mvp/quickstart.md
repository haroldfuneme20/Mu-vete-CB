# Quickstart y guía de validación: Muévete CB — MVP

**Feature**: `001-muevete-cb-mvp` | Contratos: [api.md](./contracts/api.md),
[agent.md](./contracts/agent.md), [offline-package.md](./contracts/offline-package.md) |
Datos: [data-model.md](./data-model.md)

## 1. Prerrequisitos

- Python 3.12, Node.js 20 LTS, Docker, Git + Git LFS.
- Archivos originales en `data/raw/` (P-03): barrios catastrales, trazado troncal,
  rutas provisionales, paraderos zonales SITP, estaciones TransMilenio, malla vial integrada,
  GTFS de Bogotá (zip). Rutas comunitarias simuladas en `data/seed/community_routes.geojson` y
  reportes semilla en `data/seed/seed_reports.json`.
- Teléfonos: ≥ 2 Android (Chrome) y 1 iPhone (Safari) para la validación móvil.

## 2. Construir los datos

```bash
pip install -r backend/etl/requirements.txt
python -m backend.etl.build --raw data/raw --seed data/seed \
  --db data/build/muevete.db --offline frontend/public/offline
```

Esperado: `muevete.db` creado; resumen con conteos de barrios (con cuántos de Ciudad Bolívar),
paradas, patrones, segmentos y footpaths; `frontend/public/offline/manifest.json` con tamaño
total ≤ 5 MB comprimido. El comando falla con mensaje claro si falta un archivo o un atributo
esperado (p. ej. el campo de localidad).

## 3. Ejecutar en local

```bash
# backend (sirve /api)
pip install -r backend/requirements.txt
MUEVETE_DB=data/build/muevete.db LLM_PROVIDER=mock uvicorn backend.app.main:app --port 8000

# frontend (dev, proxy /api → :8000)
cd frontend && npm ci && npm run dev
```

Verificar: `curl localhost:8000/api/health` → `"status": "ok"`, `"llm_provider": "mock"`.

## 4. Imagen de producción (igual a Render)

```bash
docker build -t muevete-cb .
docker run --rm -p 8000:8000 -m 512m muevete-cb
docker stats   # en otra terminal, durante los escenarios A-F
```

Esperado: arranque ≤ 20 s; RSS ≤ 300 MB en reposo y ≤ 450 MB en pico (P-05). Si se supera,
activar el respaldo en Hugging Face Spaces.

## 5. Pruebas automáticas

```bash
ruff check . && pytest backend agent   # motor, contratos, confirmación, reproducibilidad
cd frontend && npm run lint && npm test    # outbox, compresión de fotos
npx lhci autorun                           # accesibilidad ≥ 90 en todas las pantallas
```

## 6. Validación de escenarios (manual, en teléfono real)

| Escenario | Pasos | Resultado esperado | Criterio |
|---|---|---|---|
| **A** Ruta normal | Formulario: origen "Mirador del Paraíso", destino "Av. Jiménez", "Más rápido" → Buscar | ≤ 3 alternativas; la recomendada con tiempo, costo, confianza, fuente, paradas y explicación; tramos comunitarios marcados "simulada para la demo". Repetir 3 veces → mismo orden | SC-002, SC-003, SC-005 |
| **B** Reporte comunitario | Teléfono 1: reportar bloqueo sobre un tramo de la ruta recomendada → volver a consultar. Teléfono 2: reportar el mismo bloqueo → consultar | Tras el 1.º: más tiempo/menor confianza, cita 1 reporte. Tras el 2.º: la recomendación cambia y la explicación dice "2 personas reportaron" | SC-004 |
| **C** Offline | Modo avión → abrir la app → crear reporte con foto | Abre; se ve Ciudad Bolívar y la red troncal; "Guardado localmente. Pendiente de sincronización"; contador = 1. Cerrar y reabrir → sigue ahí | SC-006 |
| **D** Reconexión | Quitar modo avión → "Sincronizar ahora" | Reporte `synced` en ≤ 30 s; hora de última sincronización; recomendación recalculada. Repetir sincronización → sin duplicados | SC-006 |
| **E** Fallback IA | `LLM_PROVIDER=gemini` con clave inválida → repetir A | Recomendación y explicación normales; `/api/health` o la respuesta indican `explanation_provider: "mock"` | SC-009 |
| **F** Accesibilidad | TalkBack/VoiceOver activo, sin mirar: escribir/dictar "Necesito ir del barrio Paraíso al Portal Tunal, lo más confiable" → escuchar respuesta → crear un reporte | La respuesta se anuncia sola; se puede recorrer cada alternativa en texto; el reporte se completa sin ayuda | SC-007 |
| **NL** Frases | Ejecutar las 20 frases de prueba (P-08) | ≥ 18 correctas; las demás piden aclaración | SC-008 |
| **Demo completa** | Persona externa sigue el guion de 14 pasos (spec §44) | < 3 min sin ayuda | SC-001 |

## 7. Despliegue

- PR a `dev`/`main` → `ci.yml` en verde (lint, tests, build, Lighthouse).
- Push a `main` → `deploy.yml`: imagen a GHCR → deploy hook de Render → verificar
  `GET https://<servicio>.onrender.com/api/health`.
- Día del evento: activar `keepalive.yml`; generar el QR de la URL; ensayar A–F en la URL
  pública.
