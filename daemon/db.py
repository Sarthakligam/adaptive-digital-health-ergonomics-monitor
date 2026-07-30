"""
db.py — SQLite schema and connection helper for ADHEM.

Shared by the daemon (writes activity/break events) and the later
sync script (reads unsynced rows to push to AWS RDS). DB_PATH now
comes from config.py rather than being hardcoded here.

Schema includes device_id on every row (not just a single-device
assumption) — this is what lets multiple installations eventually
sync into the same cloud database without one device's rows
overwriting another's. daily_summary's primary key is now
(device_id, date) instead of just date, for the same reason: two
devices can each have their own summary row for the same calendar day.
"""

import logging
import sqlite3

import config

logger = logging.getLogger(__name__)


def get_connection():
    """Return a SQLite connection, creating the data directory if needed."""
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the events, sessions, and daily_summary tables if they don't already exist."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            event_type TEXT NOT NULL,       -- 'break_triggered' | 'break_completed' | 'break_snoozed' | 'went_idle'
            timestamp TEXT NOT NULL,        -- ISO 8601 UTC, e.g. 2026-07-12T14:03:00+00:00
            synced INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            start_time TEXT NOT NULL,       -- ISO 8601 UTC
            end_time TEXT NOT NULL,         -- ISO 8601 UTC
            duration_seconds INTEGER NOT NULL,
            ended_reason TEXT NOT NULL,     -- 'break_taken' | 'went_idle'
            synced INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS daily_summary (
            device_id TEXT NOT NULL,
            date TEXT NOT NULL,             -- 'YYYY-MM-DD'
            breaks_taken INTEGER NOT NULL DEFAULT 0,
            breaks_snoozed INTEGER NOT NULL DEFAULT 0,
            wellness_score REAL,            -- renamed from ergonomic_score — same column, clearer name
            synced INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (device_id, date)
        );
    """)
    conn.commit()
    conn.close()
    logger.info(f"Database ready at {config.DB_PATH}")


if __name__ == "__main__":
    config.setup_logging()
    init_db()
