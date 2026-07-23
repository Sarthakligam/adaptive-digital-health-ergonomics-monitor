"""
db.py — SQLite schema and connection helper for ErgoMonitor.

Shared by the daemon (writes activity/break events) and the later
sync script (reads unsynced rows to push to AWS RDS).
"""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "ergomonitor" / "ergomonitor.db"


def get_connection():
    """Return a SQLite connection, creating the project folder if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the events and daily_summary tables if they don't already exist."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,       -- 'break_triggered' | 'break_completed' | 'break_snoozed'
            timestamp TEXT NOT NULL,        -- ISO 8601, e.g. 2026-07-12T14:03:00
            synced INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS daily_summary (
            date TEXT PRIMARY KEY,          -- 'YYYY-MM-DD'
            breaks_taken INTEGER NOT NULL DEFAULT 0,
            breaks_snoozed INTEGER NOT NULL DEFAULT 0,
            ergonomic_score REAL,
            synced INTEGER NOT NULL DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()
    print(f"Database ready at {DB_PATH}")


if __name__ == "__main__":
    init_db()
