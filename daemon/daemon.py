"""
daemon.py — Wires real pynput keyboard/mouse events into the
ActivityTracker state machine, and logs break/idle events to the
local SQLite database.

Run directly to test end to end on the real machine:
    python3 daemon.py
Then type or move the mouse and watch the terminal for logged events.
Ctrl+C to stop.
"""

import threading
from datetime import datetime, timezone

from tracker import ActivityTracker
from db import get_connection, init_db


def log_event(event_type: str) -> None:
    """
    Write one row to the events table. No key content is ever read or
    stored here — only the fact that a tracker-level event occurred
    (break_triggered / went_idle) and when.
    """
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO events (event_type, timestamp) VALUES (?, ?)",
            (event_type, datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        conn.commit()
    finally:
        conn.close()


def on_trigger_break() -> None:
    print("[daemon] TRIGGER_BREAK — 20 minutes of continuous activity")
    log_event("break_triggered")


def on_go_idle() -> None:
    print("[daemon] user went idle")
    log_event("went_idle")


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
    init_db()  # safe every startup — CREATE TABLE IF NOT EXISTS

    tracker = ActivityTracker(on_trigger_break=on_trigger_break, on_go_idle=on_go_idle)
    keyboard_listener, mouse_listener = start_listeners(tracker)

    tracker_thread = threading.Thread(target=tracker.run, daemon=True)
    tracker_thread.start()

    print("[daemon] running — type or move the mouse. Ctrl+C to stop.")
    try:
        keyboard_listener.join()
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()
        keyboard_listener.stop()
        mouse_listener.stop()
        print("\n[daemon] stopped")


if __name__ == "__main__":
    main()
