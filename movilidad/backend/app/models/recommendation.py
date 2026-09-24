"""Esquemas de recomendación (T043, contracts/api.md)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from backend.app.models.common import PlaceRef

Priority = Literal["balanced", "fast", "cheap", "reliable"]


class RecommendationRequest(BaseModel):
    origin: PlaceRef | None = None
    destination: PlaceRef | None = None
    query: str | None = Field(default=None, max_length=300)
    priority: Priority = "balanced"
    depart_at: str | None = None

    @model_validator(mode="after")
    def _exactly_one(self):
        has_form = self.origin is not None and self.destination is not None
        has_query = bool(self.query and self.query.strip())
        if has_form == has_query:
            raise ValueError("Envía exactamente una forma: `query` o `origin` + `destination`")
        return self
