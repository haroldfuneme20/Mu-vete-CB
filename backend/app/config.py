"""Configuración por variables de entorno + engine.yaml / fares.yaml (T012)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "backend" / "config"


def _load_yaml(name: str) -> dict[str, Any]:
    return yaml.safe_load((CONFIG_DIR / name).read_text(encoding="utf-8"))


def _validate_engine(cfg: dict[str, Any]) -> dict[str, Any]:
    for key in ("walk", "transfers", "wait", "candidates", "reports", "weights", "availability"):
        if key not in cfg:
            raise ValueError(f"engine.yaml: falta la sección '{key}'")
    for prio, w in cfg["weights"].items():
        if len(w) != 4 or abs(sum(w) - 1.0) > 1e-6:
            raise ValueError(f"engine.yaml: los pesos de '{prio}' deben ser 4 y sumar 1")
    return cfg


@dataclass(frozen=True)
class Settings:
    db_path: Path
    work_db_path: Path
    llm_provider: str
    gemini_api_key: str | None
    groq_api_key: str | None
    photos_dir: Path
    static_dir: Path | None
    seed_dir: Path
    demo_b_backup: bool
    engine: dict[str, Any] = field(default_factory=dict)
    fares: dict[str, Any] = field(default_factory=dict)


@lru_cache
def get_settings() -> Settings:
    db = Path(os.getenv("MUEVETE_DB", ROOT / "data/build/muevete.db"))
    static = os.getenv("STATIC_DIR")
    return Settings(
        db_path=db,
        work_db_path=Path(os.getenv("MUEVETE_WORK_DB", db.with_name(db.stem + ".work.db"))),
        llm_provider=os.getenv("LLM_PROVIDER", "mock").lower(),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        groq_api_key=os.getenv("GROQ_API_KEY") or None,
        photos_dir=Path(os.getenv("PHOTOS_DIR", "/tmp/photos")),
        static_dir=Path(static) if static else None,
        seed_dir=Path(os.getenv("SEED_DIR", ROOT / "data/seed")),
        demo_b_backup=os.getenv("DEMO_B_BACKUP", "false").lower() == "true",
        engine=_validate_engine(_load_yaml("engine.yaml")),
        fares=_load_yaml("fares.yaml"),
    )
