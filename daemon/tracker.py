"""
tracker.py — Core activity-tracking state machine.

Deliberately contains NO pynput code and NO I/O. It only knows about
two things: "an input event happened" and "time has passed." That
separation is what makes it possible to test the tricky timing logic
below with a fake clock, instead of having to actually wait 20 real
minutes or fake a real keyboard.

Day 6 adds snooze_break() and on_session_end: snoozing suppresses the
next reminder for a grace period WITHOUT resetting the continuous
streak (a snoozed break doesn't erase an unhealthy long session), and
on_session_end fires whenever a session actually concludes (real break
or went idle) so the caller can log it for the wellness engine.
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
    snoozed_until: Optional[float] = None


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
        on_session_end: Callable[[float, str], None] = lambda duration, reason: None,
        clock: Callable[[], float] = time.monotonic,
        idle_timeout: float = 5 * 60,
        continuous_threshold: float = 20 * 60,
        check_interval: float = 5,
    ):
        self._state = TrackerState()
        self._lock = threading.Lock()
        self._on_trigger_break = on_trigger_break
        self._on_go_idle = on_go_idle
        self._on_session_end = on_session_end
        self._clock = clock
        self._idle_timeout = idle_timeout
        self._continuous_threshold = continuous_threshold
        self._check_interval = check_interval
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
        session_ended = None  # (duration_seconds, reason) or None
        with self._lock:
            s = self._state
            if not s.is_active:
                pass
            elif s.last_activity is not None and (now - s.last_activity) >= self._idle_timeout:
                session_ended = (s.last_activity - s.continuous_start, "went_idle")
                s.is_active = False
                s.continuous_start = None
                s.break_flag = False
                s.snoozed_until = None
                fire_idle = True
            elif not s.break_flag and s.continuous_start is not None:
                if (now - s.continuous_start) >= self._continuous_threshold:
                    if s.snoozed_until is None or now >= s.snoozed_until:
                        s.break_flag = True
                        fire_break = True

        if fire_idle:
            self._on_go_idle()
        if fire_break:
            self._on_trigger_break()
        if session_ended is not None:
            self._on_session_end(*session_ended)

    def acknowledge_break(self) -> None:
        """Call when the user completes a REAL break — ends the session and starts a fresh streak."""
        now = self._clock()
        session_ended = None
        with self._lock:
            s = self._state
            if s.continuous_start is not None:
                session_ended = (now - s.continuous_start, "break_taken")
            s.continuous_start = now
            s.break_flag = False
            s.snoozed_until = None
        if session_ended is not None:
            self._on_session_end(*session_ended)

    def snooze_break(self, grace_seconds: float) -> None:
        """
        Suppress the next reminder for grace_seconds WITHOUT resetting the
        continuous-activity streak or ending the session. Snoozing delays
        the nag — it does not erase an unhealthy long session, since the
        underlying continuous activity is still ongoing.
        """
        now = self._clock()
        with self._lock:
            self._state.break_flag = False
            self._state.snoozed_until = now + grace_seconds

    def run(self) -> None:
        """Background loop — call tick() every CHECK_INTERVAL_SECONDS until stop()."""
        while not self._stop_event.wait(self._check_interval):
            self.tick()

    def stop(self) -> None:
        self._stop_event.set()
