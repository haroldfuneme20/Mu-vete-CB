"""Restaura el estado de la demo al arrancar (T070, FR-033)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.models.report import ReportIn
from backend.app.services.reports import ReportsRepo


def load_seed_reports(repo: ReportsRepo, seed_dir: Path, include_backup: bool) -> int:
    path = seed_dir / "seed_reports.json"
    if not path.exists():
        return 0
    n = 0
    for item in json.loads(path.read_text(encoding="utf-8")):
        if item.get("backup") and not include_backup:
            continue
        data = {k: v for k, v in item.items() if k != "backup"}
        repo.upsert(ReportIn(**data), source="demo_simulated")
        n += 1
    return n
