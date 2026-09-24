"""Utilidades geográficas compartidas por el ETL y el servidor.

Las distancias en metros se calculan con una proyección equirectangular local centrada en
Bogotá; a la escala de la ciudad el error es < 0,5 %, suficiente para caminatas y radios de
reportes.
"""

from __future__ import annotations

import math
import re
import unicodedata

from shapely import affinity
from shapely.geometry.base import BaseGeometry

LAT0 = 4.60
M_PER_DEG_LAT = 110_574.0
M_PER_DEG_LNG = 111_320.0 * math.cos(math.radians(LAT0))

_PREFIXES = re.compile(r"^(el barrio|barrio|br|la estacion|estacion|est|paradero|parada)\s+")
_AVENIDA = re.compile(r"\bavenida\b")


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def deg_delta(meters: float) -> tuple[float, float]:
    """Devuelve (dlat, dlng) en grados equivalentes a `meters`."""
    return meters / M_PER_DEG_LAT, meters / M_PER_DEG_LNG


def to_local_m(geom: BaseGeometry) -> BaseGeometry:
    """Escala una geometría lng/lat a metros locales (para distancias con Shapely)."""
    return affinity.scale(geom, xfact=M_PER_DEG_LNG, yfact=M_PER_DEG_LAT, origin=(0, 0))


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def normalize_name(text: str, drop_prefix: bool = True) -> str:
    t = strip_accents(text or "").lower().strip()
    t = re.sub(r"[^a-z0-9ñ ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = _AVENIDA.sub("av", t)
    if drop_prefix:
        t = _PREFIXES.sub("", t).strip()
    return t
