"""Reportes: POST /api/reports, GET /api/reports, GET /api/reports/{id}/photo (T068)."""

from __future__ import annotations

import json

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError

from backend.app.api.errors import ApiError
from backend.app.models.report import ReportIn
from backend.app.services.photos import MAX_BYTES, PhotoError

router = APIRouter()


def parse_report(raw: str | dict) -> ReportIn:
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        return ReportIn(**data)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ApiError("VALIDATION_ERROR", "El reporte no es un JSON válido.") from exc
    except ValidationError as exc:
        raise ApiError("VALIDATION_ERROR", "Faltan datos del reporte (ubicación y categoría).",
                       {"errors": [{"loc": list(e["loc"]), "msg": e["msg"]}
                                   for e in exc.errors()]}) from exc


async def read_photo(photo: UploadFile | None) -> bytes | None:
    if photo is None:
        return None
    data = await photo.read(MAX_BYTES + 1)
    return data or None


def save_report(core, report: ReportIn, photo: bytes | None) -> tuple[str, dict]:
    path = None
    if photo:
        try:
            path = core.photos.save(report.id, photo)
        except PhotoError as e:
            raise ApiError(e.code, e.message) from e
    status, out = core.reports.upsert(report, path)
    return status, {**out, "status": status}


@router.post("/reports")
async def create_report(request: Request, report: str = Form(...),
                        photo: UploadFile | None = File(default=None)):
    core = request.app.state.core
    r = parse_report(report)
    status, out = save_report(core, r, await read_photo(photo))
    return JSONResponse(out, status_code=201 if status == "accepted" else 200)


@router.get("/reports")
def list_reports(request: Request, active: bool = True,
                 bbox: str | None = Query(default=None)) -> dict:
    box = None
    if bbox:
        try:
            box = tuple(float(x) for x in bbox.split(","))
            assert len(box) == 4
        except (ValueError, AssertionError) as exc:
            raise ApiError("VALIDATION_ERROR", "bbox = minLng,minLat,maxLng,maxLat") from exc
    return {"items": request.app.state.core.reports.list_public(active, box)}


@router.get("/reports/{report_id}/photo")
def report_photo(report_id: str, request: Request):
    p = request.app.state.core.photos.path_for(report_id)
    if p is None:
        raise ApiError("NOT_FOUND", "Este reporte no tiene foto.")
    return FileResponse(p, media_type="image/jpeg")
