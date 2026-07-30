"""Test Day 6's additions: snooze_break() and the on_session_end callback."""
from tracker import ActivityTracker


class FakeClock:
    def __init__(self):
        self.t = 0.0
    def __call__(self):
        return self.t
    def advance(self, seconds):
        self.t += seconds


def test(name, fn):
    try:
        fn()
        print(f"PASS: {name}")
    except AssertionError as e:
        print(f"FAIL: {name} -- {e}")


def test_snooze_does_not_reset_continuous_start():
    clock = FakeClock()
    triggered = []
    t = ActivityTracker(on_trigger_break=lambda: triggered.append(clock.t), clock=clock,
                         idle_timeout=300, continuous_threshold=1200)
    for _ in range(125):  # reach the 20-min threshold (~1250s)
        t.on_input_event()
        clock.advance(10)
        t.tick()
    assert len(triggered) == 1, f"expected the first trigger, got {triggered}"

    t.snooze_break(grace_seconds=300)  # 5-minute grace period
    # keep "working" through the grace period — should NOT re-trigger yet
    for _ in range(29):  # 290 seconds, just under the 300s grace period
        t.on_input_event()
        clock.advance(10)
        t.tick()
    assert len(triggered) == 1, f"should still be suppressed during grace period, got {triggered}"

    # cross the grace period boundary — continuous_start never moved, so
    # this should fire again almost immediately once grace period ends
    t.on_input_event()
    clock.advance(15)
    t.tick()
    assert len(triggered) == 2, f"expected a second trigger once grace period passed, got {triggered}"


def test_snooze_does_not_end_the_session():
    clock = FakeClock()
    session_ends = []
    t = ActivityTracker(on_trigger_break=lambda: None, on_session_end=lambda d, r: session_ends.append((d, r)),
                         clock=clock, idle_timeout=300, continuous_threshold=1200)
    for _ in range(125):
        t.on_input_event()
        clock.advance(10)
        t.tick()
    t.snooze_break(grace_seconds=300)
    assert session_ends == [], f"snoozing must not end a session, got {session_ends}"


def test_real_break_ends_session_with_correct_duration():
    clock = FakeClock()
    session_ends = []
    t = ActivityTracker(on_trigger_break=lambda: None, on_session_end=lambda d, r: session_ends.append((d, r)),
                         clock=clock, idle_timeout=300, continuous_threshold=1200)
    for _ in range(125):  # ~1250 seconds of activity
        t.on_input_event()
        clock.advance(10)
        t.tick()
    t.acknowledge_break()
    assert len(session_ends) == 1, f"expected exactly one session_end, got {session_ends}"
    duration, reason = session_ends[0]
    assert reason == "break_taken"
    assert 1240 <= duration <= 1260, f"unexpected session duration: {duration}"


def test_going_idle_ends_session_with_correct_duration():
    clock = FakeClock()
    session_ends = []
    t = ActivityTracker(on_trigger_break=lambda: None, on_session_end=lambda d, r: session_ends.append((d, r)),
                         clock=clock, idle_timeout=300, continuous_threshold=1200)
    t.on_input_event()
    clock.advance(400)  # 400s of "activity" (single event, then time passes)
    t.on_input_event()  # a second event extends last_activity
    clock.advance(600)  # now idle for 600s > 300s timeout
    t.tick()
    assert len(session_ends) == 1, f"expected exactly one session_end, got {session_ends}"
    duration, reason = session_ends[0]
    assert reason == "went_idle"
    assert 395 <= duration <= 405, f"expected duration measured to last real activity, got {duration}"


def test_backward_compatible_without_on_session_end():
    # confirms Day 2/3/4's existing usage (no on_session_end argument) still works
    clock = FakeClock()
    t = ActivityTracker(on_trigger_break=lambda: None, clock=clock)
    t.on_input_event()
    t.tick()
    t.acknowledge_break()  # should not raise, even with no on_session_end supplied
    print("PASS: backward compatible without on_session_end")


test("snooze does not reset continuous_start (re-triggers after grace period)", test_snooze_does_not_reset_continuous_start)
test("snooze does not end the session", test_snooze_does_not_end_the_session)
test("real break ends session with correct duration", test_real_break_ends_session_with_correct_duration)
test("going idle ends session with correct duration", test_going_idle_ends_session_with_correct_duration)
test_backward_compatible_without_on_session_end()
