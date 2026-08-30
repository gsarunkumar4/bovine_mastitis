import sqlite3
from pathlib import Path
DB_PATH=Path(__file__).resolve().parents[2]/"mastitis.db"

def connect():
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c

def init_db():
    c=connect()
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
      milking_hygiene_score REAL, source TEXT DEFAULT 'sensor');
    CREATE TABLE IF NOT EXISTS alerts(
      id INTEGER PRIMARY KEY AUTOINCREMENT,cow_id TEXT,timestamp TEXT,
      risk_score REAL,message TEXT,status TEXT DEFAULT 'open');
    CREATE TABLE IF NOT EXISTS feedback(
      id INTEGER PRIMARY KEY AUTOINCREMENT,cow_id TEXT,event_date TEXT,
      confirmed_mastitis INTEGER,notes TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    c.commit(); c.close()
