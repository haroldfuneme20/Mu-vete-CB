"""Fotos de reportes (T066): JPEG ≤ 1 MB en disco efímero."""

from __future__ import annotations

from pathlib import Path

MAX_BYTES = 1024 * 1024


class PhotoError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


class PhotoStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def validate(data: bytes) -> None:
        if len(data) > MAX_BYTES:
            raise PhotoError("PAYLOAD_TOO_LARGE", "La foto supera 1 MB.")
        if not data.startswith(b"\xff\xd8"):
            raise PhotoError("VALIDATION_ERROR", "La foto debe ser JPEG.")

    def save(self, report_id: str, data: bytes) -> str:
        self.validate(data)
        path = self.root / f"{report_id}.jpg"
        path.write_bytes(data)
        return str(path)

    def path_for(self, report_id: str) -> Path | None:
        p = self.root / f"{report_id}.jpg"
        return p if p.exists() else None
