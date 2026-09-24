"""Errores de dominio con la forma común de contracts/api.md (T026)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

STATUS = {
    "VALIDATION_ERROR": 422,
    "OUT_OF_COVERAGE": 422,
    "SAME_ORIGIN_DESTINATION": 422,
    "AMBIGUOUS_PLACE": 409,
    "NO_ROUTE": 404,
    "NOT_FOUND": 404,
    "PAYLOAD_TOO_LARGE": 413,
    "INTERNAL": 500,
}


class ApiError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code, self.message, self.details = code, message, details or {}


def body(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return JSONResponse(body(exc.code, exc.message, exc.details),
                            status_code=STATUS.get(exc.code, 400))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        errs = [{"loc": list(e.get("loc", [])), "msg": e.get("msg")} for e in exc.errors()]
        return JSONResponse(
            body("VALIDATION_ERROR", "Revisa los datos enviados.", {"errors": errs}),
            status_code=422)
