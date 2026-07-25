"""
Test the daemon's tracker-to-SQLite wiring with a fake clock and a
temporary database. Does NOT import pynput at all (it's deferred
inside daemon.start_listeners), so this runs fine even before pynput
is confirmed working on this machine.
"""
import tempfile
from pathlib import Path

import db
from tracker import ActivityTracker
from daemon import on_trigger_break, on_go_idle


class FakeClock:
    def __init__(self):
        self.t = 0.0
    def __call__(self):
        return self.t
    def advance(self, seconds):
        self.t += seconds


def fresh_test_db():
    db.DB_PATH = Path(tempfile.mkdtemp()) / "test_ergomonitor.db"
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
    rows = conn.execute("SELECT event_type FROM events").fetchall()
    conn.close()
    event_types = [r["event_type"] for r in rows]
    assert "break_triggered" in event_types, f"expected a logged break_triggered event, got {event_types}"
    print("PASS: trigger_break logs to sqlite")


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
