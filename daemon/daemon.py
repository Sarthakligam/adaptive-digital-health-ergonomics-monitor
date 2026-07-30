"""
daemon.py — Wires real pynput keyboard/mouse events into the
ActivityTracker state machine, and logs break/idle events to the
local SQLite database.

Run directly to test end to end on the real machine:
    python3 daemon.py
Then type or move the mouse and watch the terminal for logged events.
Ctrl+C to stop.
"""

import logging
import threading
from datetime import datetime, timedelta, timezone

import config
from tracker import ActivityTracker
from db import get_connection, init_db

logger = logging.getLogger(__name__)


def log_event(event_type: str) -> None:
    """
    Write one row to the events table, tagged with this device's
    persistent device_id. No key content is ever read or stored here —
    only the fact that a tracker-level event occurred and when.
    """
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO events (device_id, event_type, timestamp) VALUES (?, ?, ?)",
            (config.DEVICE_ID, event_type, datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        conn.commit()
    finally:
        conn.close()


def log_session(duration_seconds: float, ended_reason: str) -> None:
    """
    Write one row to the sessions table when a session actually ends
    (real break taken, or went idle) — never on snooze, since snoozing
    doesn't end the session. Timestamps are derived from "now minus
    duration" since tracker.py deliberately works in monotonic seconds,
    not wall-clock time (see tracker.py's docstring for why).
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(seconds=duration_seconds)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO sessions (device_id, start_time, end_time, duration_seconds, ended_reason) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                config.DEVICE_ID,
                start_time.isoformat(timespec="seconds"),
                end_time.isoformat(timespec="seconds"),
                int(duration_seconds),
                ended_reason,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def on_trigger_break() -> None:
    logger.info("TRIGGER_BREAK — 20 minutes of continuous activity")
    log_event("break_triggered")


def on_go_idle() -> None:
    logger.info("user went idle")
    log_event("went_idle")


def on_session_end(duration_seconds: float, reason: str) -> None:
    logger.info(f"session ended: {duration_seconds:.0f}s ({reason})")
    log_session(duration_seconds, reason)


def start_listeners(tracker: ActivityTracker):
    """
    pynput is imported *inside* this function rather than at the top
    of the file. That means log_event/on_trigger_break/on_go_idle above
    can be imported and tested on any machine, even one without pynput
    installed (or without a display at all) — the import only happens
    when this function actually runs.
    """
    from pynput import keyboard, mouse

    def on_key_press(key):
        tracker.on_input_event()

    def on_mouse_move(x, y):
        tracker.on_input_event()

    def on_mouse_click(x, y, button, pressed):
        tracker.on_input_event()

    def on_mouse_scroll(x, y, dx, dy):
        tracker.on_input_event()

    keyboard_listener = keyboard.Listener(on_press=on_key_press)
    mouse_listener = mouse.Listener(
        on_move=on_mouse_move, on_click=on_mouse_click, on_scroll=on_mouse_scroll
    )
    keyboard_listener.start()
    mouse_listener.start()
    return keyboard_listener, mouse_listener


def main() -> None:
    config.setup_logging()
    init_db()  # safe every startup — CREATE TABLE IF NOT EXISTS

    tracker = ActivityTracker(
        on_trigger_break=on_trigger_break,
        on_go_idle=on_go_idle,
        on_session_end=on_session_end,
        idle_timeout=config.IDLE_TIMEOUT_SECONDS,
        continuous_threshold=config.CONTINUOUS_THRESHOLD_SECONDS,
    )
    keyboard_listener, mouse_listener = start_listeners(tracker)

    tracker_thread = threading.Thread(target=tracker.run, daemon=True)
    tracker_thread.start()

    logger.info(f"daemon running (device_id={config.DEVICE_ID}) — Ctrl+C to stop.")
    try:
        keyboard_listener.join()
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()
        keyboard_listener.stop()
        mouse_listener.stop()
        logger.info("daemon stopped")


if __name__ == "__main__":
    main()
