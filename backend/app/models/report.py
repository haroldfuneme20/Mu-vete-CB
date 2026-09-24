"""Esquemas de reportes ciudadanos (T064)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["blockage", "delay", "route_change", "risk", "other"]

# Caja amplia de Bogotá para validar ubicaciones
BOGOTA_BBOX = (3.7, 4.95, -74.5, -73.95)   # lat_min, lat_max, lng_min, lng_max


class Location(BaseModel):
    lat: float = Field(ge=BOGOTA_BBOX[0], le=BOGOTA_BBOX[1])
    lng: float = Field(ge=BOGOTA_BBOX[2], le=BOGOTA_BBOX[3])


class ReportIn(BaseModel):
    id: str = Field(pattern=r"^[0-9a-fA-F-]{8,64}$")
    anon_id: str = Field(pattern=r"^[0-9a-fA-F-]{8,64}$")
    category: Category
    location: Location
    description: str | None = Field(default=None, max_length=280)
    created_at: str | None = None
