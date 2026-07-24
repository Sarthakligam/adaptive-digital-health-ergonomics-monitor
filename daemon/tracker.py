"""
tracker.py — Core activity-tracking state machine.

Deliberately contains NO pynput code and NO I/O. It only knows about
two things: "an input event happened" and "time has passed." That
separation is what makes it possible to test the tricky timing logic
below with a fake clock, instead of having to actually wait 20 real
minutes or fake a real keyboard. Day 3 wires this up to real pynput
events and real SQLite logging.
"""

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

IDLE_TIMEOUT_SECONDS = 5 * 60            # 5 min idle -> streak resets
CONTINUOUS_THRESHOLD_SECONDS = 20 * 60   # 20 min continuous -> trigger break
CHECK_INTERVAL_SECONDS = 5               # how often the background loop checks


@dataclass
class TrackerState:
    is_active: bool = False
    continuous_start: Optional[float] = None
    last_activity: Optional[float] = None
    break_flag: bool = False


class ActivityTracker:
    """
    Feed it activity via on_input_event() (called from pynput callbacks
    on Day 3). Call tick() periodically — or let run() do it on a
    background thread — to evaluate idle/continuous state.
    """

    def __init__(
        self,
        on_trigger_break: Callable[[], None],
        on_go_idle: Callable[[], None] = lambda: None,
        clock: Callable[[], float] = time.monotonic,
        idle_timeout: float = IDLE_TIMEOUT_SECONDS,
        continuous_threshold: float = CONTINUOUS_THRESHOLD_SECONDS,
    ):
        self._state = TrackerState()
        self._lock = threading.Lock()
        self._on_trigger_break = on_trigger_break
        self._on_go_idle = on_go_idle
        self._clock = clock
        self._idle_timeout = idle_timeout
        self._continuous_threshold = continuous_threshold
        self._stop_event = threading.Event()

    def on_input_event(self) -> None:
        now = self._clock()
        with self._lock:
            self._state.last_activity = now
            if not self._state.is_active:
                self._state.is_active = True
                self._state.continuous_start = now

    def tick(self) -> None:
        now = self._clock()
        fire_idle = False
        fire_break = False
        with self._lock:
            s = self._state
            if not s.is_active:
                pass
            elif s.last_activity is not None and (now - s.last_activity) >= self._idle_timeout:
                s.is_active = False
                s.continuous_start = None
                s.break_flag = False
                fire_idle = True
            elif not s.break_flag and s.continuous_start is not None:
                if (now - s.continuous_start) >= self._continuous_threshold:
                    s.break_flag = True
                    fire_break = True

        if fire_idle:
            self._on_go_idle()
        if fire_break:
            self._on_trigger_break()

    def acknowledge_break(self) -> None:
        """Call when the user completes or snoozes a break — starts a fresh streak."""
        now = self._clock()
        with self._lock:
            self._state.continuous_start = now
            self._state.break_flag = False

    def run(self) -> None:
        """Background loop — call tick() every CHECK_INTERVAL_SECONDS until stop()."""
        while not self._stop_event.wait(CHECK_INTERVAL_SECONDS):
            self.tick()

    def stop(self) -> None:
        self._stop_event.set()
