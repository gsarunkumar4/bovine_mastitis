"""
§2 — Cloud-storage readiness layer.

Provides a pluggable StorageBackend interface with a working free/local
implementation (LocalStorageBackend) that creates timestamped SQLite
backups and CSV exports.  A paid cloud backend (S3, GCS, etc.) can be
swapped in by implementing the same interface and setting
STORAGE_BACKEND in config.py.
"""

import csv
import io
import shutil
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from config import DATABASE_PATH, ROOT


# ── default backup directory ────────────────────────────────────────
BACKUP_DIR = ROOT / "data" / "backups"


# ── abstract interface ──────────────────────────────────────────────

class StorageBackend(ABC):
    """Pluggable storage interface for backup / export operations."""

    @abstractmethod
    def export_backup(self) -> dict:
        """Create a full backup.  Returns metadata dict."""

    @abstractmethod
    def list_backups(self) -> list[dict]:
        """Return metadata for all existing backups."""

    @abstractmethod
    def status(self) -> dict:
        """Return backend type and health info."""


# ── local (SQLite copy + CSV) implementation ────────────────────────

class LocalStorageBackend(StorageBackend):
    """
    Free / local backup backend.

    • Copies the live SQLite file to data/backups/<timestamp>.db
    • Exports each table as a CSV alongside it
    """

    def __init__(self, backup_dir: Path | None = None):
        self.backup_dir = backup_dir or BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------------

    def export_backup(self) -> dict:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        prefix = self.backup_dir / ts

        # 1. Raw SQLite copy
        db_dest = prefix.with_suffix(".db")
        shutil.copy2(DATABASE_PATH, db_dest)

        # 2. Per-table CSV export
        csv_files: list[str] = []
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            ]
            for tbl in tables:
                rows = conn.execute(f"SELECT * FROM {tbl}").fetchall()  # noqa: S608
                if not rows:
                    continue
                csv_path = self.backup_dir / f"{ts}_{tbl}.csv"
                with open(csv_path, "w", newline="", encoding="utf-8") as fh:
                    writer = csv.writer(fh)
                    writer.writerow(rows[0].keys())
                    writer.writerows(tuple(r) for r in rows)
                csv_files.append(str(csv_path))
        finally:
            conn.close()

        size_bytes = db_dest.stat().st_size

        return {
            "timestamp": ts,
            "db_file": str(db_dest),
            "csv_files": csv_files,
            "size_bytes": size_bytes,
            "backend": "local",
        }

    # ----------------------------------------------------------------

    def list_backups(self) -> list[dict]:
        out: list[dict] = []
        for p in sorted(self.backup_dir.glob("*.db"), reverse=True):
            out.append({
                "file": str(p),
                "timestamp": p.stem,
                "size_bytes": p.stat().st_size,
            })
        return out

    # ----------------------------------------------------------------

    def status(self) -> dict:
        backups = self.list_backups()
        return {
            "backend": "local",
            "backup_dir": str(self.backup_dir),
            "total_backups": len(backups),
            "last_backup": backups[0]["timestamp"] if backups else None,
            "note": (
                "Local storage backend.  Data is backed up to "
                "timestamped SQLite + CSV files.  For production, "
                "configure STORAGE_BACKEND to a cloud provider."
            ),
        }


# ── factory ─────────────────────────────────────────────────────────

_BACKENDS = {
    "local": LocalStorageBackend,
}


def get_backend(name: str = "local") -> StorageBackend:
    """Return configured StorageBackend instance."""
    cls = _BACKENDS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown storage backend '{name}'.  "
            f"Available: {list(_BACKENDS.keys())}"
        )
    return cls()
