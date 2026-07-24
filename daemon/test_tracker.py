"""Test tracker.py with a fake clock — no real waiting, no real pynput needed."""
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

def test_no_events_never_triggers():
    clock = FakeClock()
    triggered = []
    t = ActivityTracker(on_trigger_break=lambda: triggered.append(1), clock=clock)
    for _ in range(10):
        clock.advance(300)
        t.tick()
    assert triggered == [], f"expected no triggers, got {triggered}"

def test_continuous_use_triggers_at_threshold():
    clock = FakeClock()
    triggered = []
    t = ActivityTracker(on_trigger_break=lambda: triggered.append(clock.t), clock=clock,
                         idle_timeout=300, continuous_threshold=1200)
    # simulate a keypress every 10 seconds for 25 minutes straight
    for _ in range(150):
        t.on_input_event()
        clock.advance(10)
        t.tick()
    assert len(triggered) == 1, f"expected exactly 1 trigger, got {len(triggered)}: {triggered}"
    assert 1200 <= triggered[0] <= 1210, f"triggered at wrong time: {triggered[0]}"

def test_break_does_not_refire_until_acknowledged():
    clock = FakeClock()
    triggered = []
    t = ActivityTracker(on_trigger_break=lambda: triggered.append(clock.t), clock=clock,
                         idle_timeout=300, continuous_threshold=1200)
    for _ in range(200):  # 2000+ seconds of continuous "typing", well past threshold
        t.on_input_event()
        clock.advance(10)
        t.tick()
    assert len(triggered) == 1, f"break_flag should prevent re-firing, got {len(triggered)}: {triggered}"

def test_acknowledge_starts_fresh_streak():
    clock = FakeClock()
    triggered = []
    t = ActivityTracker(on_trigger_break=lambda: triggered.append(clock.t), clock=clock,
                         idle_timeout=300, continuous_threshold=1200)
    for _ in range(125):  # reach the first trigger (~1250s)
        t.on_input_event()
        clock.advance(10)
        t.tick()
    assert len(triggered) == 1
    t.acknowledge_break()
    for _ in range(125):  # another ~1250s of continuous use after acknowledging
        t.on_input_event()
        clock.advance(10)
        t.tick()
    assert len(triggered) == 2, f"expected a second trigger after acknowledge, got {triggered}"

def test_idle_resets_streak_and_fires_go_idle():
    clock = FakeClock()
    went_idle = []
    t = ActivityTracker(on_trigger_break=lambda: None, on_go_idle=lambda: went_idle.append(clock.t),
                         clock=clock, idle_timeout=300, continuous_threshold=1200)
    t.on_input_event()
    clock.advance(600)  # 10 minutes idle, well past the 5-minute timeout
    t.tick()
    assert went_idle == [600.0], f"expected go_idle at t=600, got {went_idle}"

def test_idle_then_new_activity_needs_full_threshold_again():
    clock = FakeClock()
    triggered = []
    t = ActivityTracker(on_trigger_break=lambda: triggered.append(clock.t), clock=clock,
                         idle_timeout=300, continuous_threshold=1200)
    # 15 minutes of activity (under threshold)
    for _ in range(90):
        t.on_input_event()
        clock.advance(10)
        t.tick()
    assert triggered == []
    # go idle for 10 minutes
    clock.advance(600)
    t.tick()
    # resume — should need another full 20 minutes, not just the remaining 5
    for _ in range(90):  # another 15 min — should NOT be enough
        t.on_input_event()
        clock.advance(10)
        t.tick()
    assert triggered == [], f"streak should have reset after idle, got {triggered}"

test("no events never triggers", test_no_events_never_triggers)
test("continuous use triggers at threshold", test_continuous_use_triggers_at_threshold)
test("break does not refire until acknowledged", test_break_does_not_refire_until_acknowledged)
test("acknowledge starts fresh streak", test_acknowledge_starts_fresh_streak)
test("idle resets streak and fires go_idle", test_idle_resets_streak_and_fires_go_idle)
test("idle then new activity needs full threshold again", test_idle_then_new_activity_needs_full_threshold_again)
