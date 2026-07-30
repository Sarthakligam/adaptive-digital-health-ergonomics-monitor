"""
Test the daemon's tracker-to-SQLite wiring with a fake clock and a
temporary database. Does NOT import pynput at all (it's deferred
inside daemon.start_listeners), so this runs fine even before pynput
is confirmed working on this machine.
"""
import tempfile
from pathlib import Path

import config
import db
from tracker import ActivityTracker
from daemon import on_trigger_break, on_go_idle, on_session_end


class FakeClock:
    def __init__(self):
        self.t = 0.0
    def __call__(self):
        return self.t
    def advance(self, seconds):
        self.t += seconds


def fresh_test_db():
    config.DB_PATH = Path(tempfile.mkdtemp()) / "test_adhem.db"
    db.init_db()


def test_trigger_break_logs_to_sqlite():
    fresh_test_db()
    clock = FakeClock()
    tracker = ActivityTracker(on_trigger_break=on_trigger_break, on_go_idle=on_go_idle,
                               clock=clock, idle_timeout=300, continuous_threshold=1200)
    for _ in range(125):  # ~1250 seconds of continuous simulated typing
        tracker.on_input_event()
        clock.advance(10)
        tracker.tick()

    conn = db.get_connection()
    rows = conn.execute("SELECT device_id, event_type FROM events").fetchall()
    conn.close()
    event_types = [r["event_type"] for r in rows]
    assert "break_triggered" in event_types, f"expected a logged break_triggered event, got {event_types}"
    assert all(r["device_id"] == config.DEVICE_ID for r in rows), "every row should be tagged with this device's id"
    print("PASS: trigger_break logs to sqlite, tagged with device_id")


def test_go_idle_logs_to_sqlite():
    fresh_test_db()
    clock = FakeClock()
    tracker = ActivityTracker(on_trigger_break=on_trigger_break, on_go_idle=on_go_idle,
                               clock=clock, idle_timeout=300, continuous_threshold=1200)
    tracker.on_input_event()
    clock.advance(600)  # 10 minutes idle, past the 5-minute timeout
    tracker.tick()

    conn = db.get_connection()
    rows = conn.execute("SELECT event_type FROM events").fetchall()
    conn.close()
    event_types = [r["event_type"] for r in rows]
    assert "went_idle" in event_types, f"expected a logged went_idle event, got {event_types}"
    print("PASS: go_idle logs to sqlite")


def test_daemon_importable_without_pynput():
    # if this file's imports succeeded at all, this already proves it —
    # but assert explicitly so the intent is on record as a real test.
    import sys
    assert "pynput" not in sys.modules, "pynput should NOT be imported by just importing daemon.py"
    print("PASS: daemon.py imports without pulling in pynput")


test_daemon_importable_without_pynput()
test_trigger_break_logs_to_sqlite()
test_go_idle_logs_to_sqlite()


def test_real_break_logs_a_session_row():
    fresh_test_db()
    clock = FakeClock()
    tracker = ActivityTracker(on_trigger_break=on_trigger_break, on_go_idle=on_go_idle,
                               on_session_end=on_session_end, clock=clock,
                               idle_timeout=300, continuous_threshold=1200)
    for _ in range(125):
        tracker.on_input_event()
        clock.advance(10)
        tracker.tick()
    tracker.acknowledge_break()

    conn = db.get_connection()
    rows = conn.execute("SELECT device_id, ended_reason, duration_seconds FROM sessions").fetchall()
    conn.close()
    assert len(rows) == 1, f"expected exactly one session row, got {rows}"
    assert rows[0]["ended_reason"] == "break_taken"
    assert rows[0]["device_id"] == config.DEVICE_ID
    assert 1240 <= rows[0]["duration_seconds"] <= 1260
    print("PASS: a real break logs a row in the sessions table")


def test_snooze_logs_no_session_row():
    fresh_test_db()
    clock = FakeClock()
    tracker = ActivityTracker(on_trigger_break=on_trigger_break, on_go_idle=on_go_idle,
                               on_session_end=on_session_end, clock=clock,
                               idle_timeout=300, continuous_threshold=1200)
    for _ in range(125):
        tracker.on_input_event()
        clock.advance(10)
        tracker.tick()
    tracker.snooze_break(grace_seconds=300)

    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM sessions").fetchall()
    conn.close()
    assert rows == [], f"snoozing must not create a session row, got {rows}"
    print("PASS: snoozing does not log a session row (session is still ongoing)")


test_real_break_logs_a_session_row()
test_snooze_logs_no_session_row()
