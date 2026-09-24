# Respaldo: Hugging Face Spaces (Docker)

Usar si Render falla o si el contenedor supera la RAM del plan gratuito (constitución,
contingencia).

1. Crear un Space de tipo **Docker** (público; 2 vCPU / 16 GB en el plan gratuito).
2. Subir el mismo repositorio (o solo `Dockerfile`, `backend/`, `agent/`, `frontend/`, `data/`).
3. En el `README.md` del Space, cabecera YAML con `sdk: docker` y `app_port: 8000`.
4. Variables del Space: `LLM_PROVIDER`, claves de API si aplica, `DATA_MODE` como build arg
   (`mock` o `real`).
5. URL resultante: `https://<usuario>-<space>.hf.space` → regenerar el QR del pitch.

No requiere cambios de código: es la misma imagen.
