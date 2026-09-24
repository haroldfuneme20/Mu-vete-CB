"""App FastAPI: /api + estáticos de la PWA con fallback de SPA (T027)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api import errors, health, places, recommendations, reports, routes, stops, sync
from backend.app.config import Settings, get_settings
from backend.app.core import Core

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def create_app(settings: Settings | None = None, core: Core | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if getattr(app.state, "core", None) is None:
            app.state.core = Core(settings)
        yield

    app = FastAPI(title="Muévete CB API", version="0.1.0", lifespan=lifespan)
    app.state.core = core
    errors.install(app)

    api = APIRouter(prefix="/api")
    for r in (health, places, recommendations, reports, sync, stops, routes):
        api.include_router(r.router)
    app.include_router(api)

    static: Path | None = settings.static_dir
    if static and static.exists():
        assets = static / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str):
            if path.startswith("api/"):
                return JSONResponse(errors.body("NOT_FOUND", "Ruta de API inexistente."), 404)
            f = (static / path).resolve()
            if path and f.is_file() and static.resolve() in f.parents:
                return FileResponse(f)
            return FileResponse(static / "index.html")

    return app


app = create_app()
