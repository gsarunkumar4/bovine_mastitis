from pathlib import Path
import sqlite3


ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "mastitis.db"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    c = connect()

    # =========================================================
    # COWS TABLE
    # =========================================================
    c.execute("""
        CREATE TABLE IF NOT EXISTS cows(
            cow_id TEXT PRIMARY KEY,
            breed TEXT,
            age_years REAL,
            parity INTEGER NOT NULL,
            calving_date TEXT,
            vaccination_status INTEGER DEFAULT 1,
            prior_mastitis_flag INTEGER DEFAULT 0,
            herd_id TEXT DEFAULT 'demo_herd_01'
        )
    """)

    # =========================================================
    # READINGS TABLE
    # =========================================================
    c.execute("""
        CREATE TABLE IF NOT EXISTS readings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cow_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,

            milk_yield_l REAL NOT NULL,
            milk_conductivity REAL NOT NULL,
            milk_temp_c REAL NOT NULL,

            scc_value REAL,

            activity_score REAL,
            rumination_min REAL,
            environment_heat_index REAL,

            hygiene_score REAL,
            feed_score REAL,
            milking_hygiene_score REAL,

            farm_temperature_c REAL,
            farm_humidity REAL,

            source TEXT DEFAULT 'sensor'
        )
    """)

    # =========================================================
    # ALERTS TABLE
    # =========================================================
    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cow_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            risk_score REAL NOT NULL,
            message TEXT NOT NULL
        )
    """)

    # =========================================================
    # FEEDBACK TABLE
    # =========================================================
    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cow_id TEXT NOT NULL,
            event_date TEXT,
            confirmed_mastitis INTEGER,
            notes TEXT
        )
    """)

    # =========================================================
    # DATABASE MIGRATION
    # =========================================================
    # If the database already existed before DHT22 support,
    # add the new columns without deleting old readings.
    existing_columns = {
        row["name"]
        for row in c.execute(
            "PRAGMA table_info(readings)"
        ).fetchall()
    }

    if "farm_temperature_c" not in existing_columns:
        c.execute("""
            ALTER TABLE readings
            ADD COLUMN farm_temperature_c REAL
        """)

    if "farm_humidity" not in existing_columns:
        c.execute("""
            ALTER TABLE readings
            ADD COLUMN farm_humidity REAL
        """)

    c.commit()
    c.close()