"""POST /api/sync (T078): lote idempotente del outbox (máx. 20)."""

from __future__ import annotations

import json

from fastapi import APIRouter, Request
from starlette.datastructures import UploadFile

from backend.app.api.errors import ApiError
from backend.app.api.reports import parse_report, save_report
from backend.app.services.photos import MAX_BYTES

router = APIRouter()
MAX_BATCH = 20


@router.post("/sync")
async def sync(request: Request) -> dict:
    core = request.app.state.core
    form = await request.form()
    raw = form.get("reports")
    try:
        items = json.loads(raw) if isinstance(raw, str) else None
    except json.JSONDecodeError:
        items = None
    if not isinstance(items, list):
        raise ApiError("VALIDATION_ERROR", "Envía `reports` como una lista JSON.")
    if len(items) > MAX_BATCH:
        raise ApiError("VALIDATION_ERROR", f"Máximo {MAX_BATCH} reportes por lote.")

    results, changed = [], False
    for item in items:
        rid = item.get("id") if isinstance(item, dict) else None
        try:
            report = parse_report(item)
            photo = form.get(f"photo_{report.id}")
            data = await photo.read(MAX_BYTES + 1) if isinstance(photo, UploadFile) else None
            status, _ = save_report(core, report, data or None)
            changed = changed or status == "accepted"
            results.append({"id": report.id, "status": status})
        except ApiError as e:
            results.append({"id": rid, "status": "rejected",
                            "error": {"code": e.code, "message": e.message}})
    return {"results": results, "server_time": core.now().isoformat(), "recalculate": changed}
