"""Lectura en streaming de archivos GTFS dentro del zip."""

from __future__ import annotations

import csv
import io
import zipfile
from collections.abc import Iterator
from pathlib import Path


class GTFS:
    def __init__(self, path: Path):
        self.zf = zipfile.ZipFile(path)
        self.names = {Path(n).name: n for n in self.zf.namelist()}

    def has(self, name: str) -> bool:
        return name in self.names

    def rows(self, name: str) -> Iterator[dict[str, str]]:
        if name not in self.names:
            return iter(())
        raw = self.zf.open(self.names[name])
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        return (
            {k.strip(): (v or "").strip() for k, v in row.items()}
            for row in csv.DictReader(text)
        )


def hms_to_s(t: str) -> int:
    h, m, s = (t.split(":") + ["0", "0"])[:3]
    return int(h) * 3600 + int(m) * 60 + int(s)
