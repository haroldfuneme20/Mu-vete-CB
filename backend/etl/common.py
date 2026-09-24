"""Utilidades del ETL: lectura de GeoJSON, reproyección, registro de fuentes y errores."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

ETL_DIR = Path(__file__).resolve().parent


class ETLError(RuntimeError):
    """Error con mensaje claro para quien prepara los datos (P-03/P-04)."""


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def load_sources_config(path: Path | None = None) -> dict[str, Any]:
    path = path or ETL_DIR / "sources.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def require_file(raw: Path, name: str) -> Path:
    p = raw / name
    if not p.exists():
        raise ETLError(
            f"Falta el archivo '{name}' en {raw}. Revisa data/raw/README.md y "
            "backend/etl/sources.yaml (P-03)."
        )
    return p


def _crs_transformer(fc: dict[str, Any]):
    crs = (fc.get("crs") or {}).get("properties", {}).get("name", "")
    if not crs or "4326" in crs or "CRS84" in crs:
        return None
    try:
        from pyproj import Transformer
    except ImportError as exc:  # pragma: no cover
        raise ETLError(f"El archivo usa el CRS {crs}; instala pyproj para reproyectar") from exc
    tr = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    return tr.transform


def read_features(path: Path, required_fields: list[str]) -> list[tuple[dict, BaseGeometry]]:
    """Lee un GeoJSON y devuelve (propiedades, geometría WGS84). Valida los atributos."""
    fc = json.loads(path.read_text(encoding="utf-8"))
    tr = _crs_transformer(fc)
    out = []
    for i, feat in enumerate(fc.get("features", [])):
        props = feat.get("properties") or {}
        missing = [f for f in required_fields if f not in props]
        if missing:
            raise ETLError(
                f"{path.name}: el feature #{i} no tiene los atributos {missing}. "
                f"Atributos disponibles: {sorted(props)}. Ajusta backend/etl/sources.yaml (P-04)."
            )
        if not feat.get("geometry"):
            continue
        geom = shape(feat["geometry"])
        if tr is not None:
            geom = transform(tr, geom)
        out.append((props, geom))
    return out


def register_source(con: sqlite3.Connection, sid: str, name: str, file: str, kind: str,
                    mock: bool) -> str:
    label = f"{name} (MOCK)" if mock else name
    con.execute(
        "INSERT OR REPLACE INTO sources(id, name, file, kind, published_at, loaded_at) "
        "VALUES (?,?,?,?,?,?)",
        (sid, label, file, kind, None, now_iso()),
    )
    return sid


def rtree_insert(con: sqlite3.Connection, table: str, rid: int, geom: BaseGeometry) -> None:
    minx, miny, maxx, maxy = geom.bounds
    con.execute(f"INSERT INTO {table} VALUES (?,?,?,?,?)", (rid, minx, maxx, miny, maxy))


class Grid:
    """Índice de celdas para búsquedas de vecinos en memoria durante el ETL."""

    def __init__(self, cell_deg: float = 0.003):
        self.cell = cell_deg
        self.cells: dict[tuple[int, int], list[Any]] = {}

    def _key(self, lat: float, lng: float) -> tuple[int, int]:
        return int(lat // self.cell), int(lng // self.cell)

    def add(self, lat: float, lng: float, item: Any) -> None:
        self.cells.setdefault(self._key(lat, lng), []).append(item)

    def near(self, lat: float, lng: float):
        ki, kj = self._key(lat, lng)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                yield from self.cells.get((ki + di, kj + dj), [])
