# Despliegue en Render (T109)

Un único **Web Service** que ejecuta la imagen Docker publicada en GHCR por `deploy.yml`.

## Configuración (una sola vez)

1. En GitHub → *Settings → Packages*: hacer pública la imagen `ghcr.io/<org>/muevete-cb`
   (o configurar credenciales de registro privado en Render).
2. En Render → *New → Web Service → Existing image*: `ghcr.io/<org>/muevete-cb:latest`.
   - Plan: Free (512 MB). Región: la más cercana disponible.
   - Health check path: `/api/health`.
   - Variables de entorno: `LLM_PROVIDER=mock` (o `gemini`/`groq` + su clave),
     `DEMO_B_BACKUP=false`. `PORT` lo define Render.
3. Copiar el **Deploy Hook** del servicio (*Settings → Deploy Hook*) y guardarlo en GitHub como
   secreto `RENDER_DEPLOY_HOOK`.
4. En GitHub → *Settings → Variables*: `PUBLIC_URL=https://<servicio>.onrender.com`
   (lo usan `deploy.yml` y `keepalive.yml`).
5. Opcional: `GTFS_RELEASE_URL` si el GTFS se publica como asset de un Release en lugar de LFS.

## Operación

- Cada push a `main` construye la imagen (ETL → PWA → runtime) y dispara el deploy.
- El disco es efímero: la base se restaura desde la imagen en cada arranque (reportes semilla
  incluidos). Los reportes de la sesión viven mientras el servicio esté activo.
- Plan gratuito: el servicio se duerme por inactividad. Durante el evento: variable
  `KEEPALIVE=on` (activa `keepalive.yml`) o plan Starter. Antes del pitch:
  `curl $PUBLIC_URL/api/health`.
- RAM: presupuesto ≤ 300 MB en reposo y ≤ 450 MB en pico (ver `docs/architecture/memory.md`).
  Si se supera, usar el respaldo `docs/deploy/hf-spaces.md`.
