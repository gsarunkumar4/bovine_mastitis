import sqlite3
from pathlib import Path
from config import DATABASE_PATH

DB_PATH = DATABASE_PATH


def connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db():
    c = connect()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS cows(
      cow_id TEXT PRIMARY KEY, breed TEXT, age_years INTEGER, parity INTEGER NOT NULL,
      calving_date TEXT, vaccination_status INTEGER DEFAULT 1,
      prior_mastitis_flag INTEGER DEFAULT 0, herd_id TEXT DEFAULT 'demo_herd_01');
    CREATE TABLE IF NOT EXISTS readings(
      id INTEGER PRIMARY KEY AUTOINCREMENT, cow_id TEXT NOT NULL, timestamp TEXT NOT NULL,
      milk_yield_l REAL NOT NULL, milk_conductivity REAL NOT NULL, milk_temp_c REAL NOT NULL,
      scc_value REAL, activity_score REAL, rumination_min REAL,
      environment_heat_index REAL, hygiene_score REAL, feed_score REAL,
      milking_hygiene_score REAL, source TEXT DEFAULT 'sensor',
      FOREIGN KEY(cow_id) REFERENCES cows(cow_id));
    CREATE TABLE IF NOT EXISTS alerts(
      id INTEGER PRIMARY KEY AUTOINCREMENT,cow_id TEXT,timestamp TEXT,
      risk_score REAL,message TEXT,status TEXT DEFAULT 'open',
      resolved_at TEXT, resolved_note TEXT);
    CREATE TABLE IF NOT EXISTS feedback(
      id INTEGER PRIMARY KEY AUTOINCREMENT,cow_id TEXT,event_date TEXT,
      confirmed_mastitis INTEGER,notes TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE INDEX IF NOT EXISTS idx_readings_cow_ts ON readings(cow_id, timestamp);
    CREATE INDEX IF NOT EXISTS idx_alerts_cow ON alerts(cow_id, status);
    """)
    c.commit()

    # ── additive schema migrations (backward-compatible) ──────────────
    # SQLite doesn't support ADD COLUMN IF NOT EXISTS, so we catch the
    # duplicate-column error silently for each new column.
    _migrate_columns = [
        # New sensor columns for latest ESP32 (DHT22) and future sensors
        ("readings", "farm_temperature_c", "REAL"),
        ("readings", "farm_humidity", "REAL"),
        ("readings", "milk_pH", "REAL"),
        ("readings", "body_temperature", "REAL"),
        ("readings", "udder_surface_temperature", "REAL"),
        # Model version tracking in alerts
        ("alerts", "model_version", "TEXT"),
    ]
    for table, col, dtype in _migrate_columns:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {dtype}")
        except sqlite3.OperationalError:
            pass  # column already exists — expected on subsequent runs

    c.commit()
    c.close()
