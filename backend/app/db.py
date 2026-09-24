"""Base SQLite de trabajo (T023).

Al arrancar se copia `muevete.db` (generada por el ETL) a un archivo de trabajo: así cada
arranque restaura el estado de la demo (FR-033) y el disco efímero de Render no importa.
"""

from __future__ import annotations

import shutil
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, source: Path, work: Path):
        if not source.exists():
            raise RuntimeError(
                f"No existe la base {source}. Ejecuta: python -m backend.etl.build --mock "
                "(o con datos reales) antes de arrancar el servidor."
            )
        work.parent.mkdir(parents=True, exist_ok=True)
        if work.resolve() != source.resolve():
            shutil.copyfile(source, work)
        self.path = work
        self._lock = threading.Lock()
        self.check_rtree()

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, check_same_thread=False, timeout=10)
        con.row_factory = sqlite3.Row
        return con

    @contextmanager
    def read(self):
        con = self.connect()
        try:
            yield con
        finally:
            con.close()

    @contextmanager
    def write(self):
        with self._lock:
            con = self.connect()
            try:
                yield con
                con.commit()
            finally:
                con.close()

    def check_rtree(self) -> None:
        con = sqlite3.connect(":memory:")
        try:
            con.execute("CREATE VIRTUAL TABLE t USING rtree(id, a, b)")
        except sqlite3.OperationalError as exc:  # pragma: no cover
            raise RuntimeError("SQLite no tiene el módulo R*Tree habilitado") from exc
        finally:
            con.close()

    def meta(self, key: str, default: str = "") -> str:
        with self.read() as con:
            row = con.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default
