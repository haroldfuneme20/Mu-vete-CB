"""Esquemas comunes (contracts/api.md)."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorBody(BaseModel):
    error: ErrorDetail


class PlaceRef(BaseModel):
    ref_id: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    label: str | None = None
    text: str | None = None

    @model_validator(mode="after")
    def _one_form(self):
        if not (self.ref_id or (self.lat is not None and self.lng is not None) or self.text):
            raise ValueError("Indica ref_id, lat/lng o text")
        return self


class Evidence(BaseModel):
    kind: str
    label: str
    source_id: str | None = None
    report_ids: list[str] | None = None
    date: str | None = None
