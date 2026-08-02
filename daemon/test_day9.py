"""Test Day 9: profiles.py, adaptive.py, suggestions.py."""
import random
import tempfile
from pathlib import Path

import config
import db
import profiles
from wellness import compute_daily_wellness
from adaptive import get_todays_threshold
from suggestions import SuggestionRotator

DEVICE = "test-device"


def fresh_test_env():
    config.DATA_DIR = Path(tempfile.mkdtemp())
    config.DB_PATH = config.DATA_DIR / "test.db"
    db.init_db()


# ---------- profiles.py ----------

def test_unknown_profile_falls_back_to_default():
    p = profiles.get_profile("astronaut")
    assert p.key == profiles.DEFAULT_PROFILE_KEY
    print("PASS: an unknown profile key safely falls back to the default")


def test_setting_and_reading_active_profile_persists():
    fresh_test_env()
    assert profiles.get_active_profile_key() == profiles.DEFAULT_PROFILE_KEY
    profiles.set_active_profile("student")
    assert profiles.get_active_profile_key() == "student"
    print("PASS: setting the active profile persists across calls")


def test_setting_invalid_profile_raises():
    fresh_test_env()
    try:
        profiles.set_active_profile("astronaut")
        assert False, "expected a ValueError for an invalid profile key"
    except ValueError:
        pass
    print("PASS: setting an invalid profile key raises instead of silently accepting it")


# ---------- adaptive.py ----------

def test_threshold_tightens_after_a_high_risk_day():
    fresh_test_env()
    profiles.set_active_profile("developer")  # baseline 1200s
    # simulate a genuinely bad day yesterday: two long sessions AND poor
    # break compliance — matches how Day 7's own tests reached High risk;
    # a single long session alone only reaches Moderate by design (capped
    # per-session penalty), which is validated, correct behavior.
    conn = db.get_connection()
    for start, end in [
        ("2026-06-14T09:00:00+00:00", "2026-06-14T10:30:00+00:00"),
        ("2026-06-14T11:00:00+00:00", "2026-06-14T12:30:00+00:00"),
    ]:
        conn.execute(
            "INSERT INTO sessions (device_id, start_time, end_time, duration_seconds, ended_reason) "
            "VALUES (?, ?, ?, ?, ?)",
            (DEVICE, start, end, 5400, "went_idle"),
        )
    for _ in range(3):
        conn.execute(
            "INSERT INTO events (device_id, event_type, timestamp) VALUES (?, ?, ?)",
            (DEVICE, "break_triggered", "2026-06-14T09:30:00+00:00"),
        )
    conn.commit()
    conn.close()

    yesterday_check = compute_daily_wellness(DEVICE, "2026-06-14")
    assert yesterday_check.fatigue_risk == "High", f"test setup should produce High risk, got {yesterday_check}"

    result = get_todays_threshold(DEVICE, today="2026-06-15")
    assert result["threshold_seconds"] < result["baseline_seconds"], result
    assert "Tightened" in result["reason"]
    print(f"PASS: threshold tightens after a High-risk day ({result})")


def test_threshold_stays_at_baseline_after_a_good_day():
    fresh_test_env()
    profiles.set_active_profile("student")  # baseline 1500s
    conn = db.get_connection()
    conn.execute(
        "INSERT INTO sessions (device_id, start_time, end_time, duration_seconds, ended_reason) "
        "VALUES (?, ?, ?, ?, ?)",
        (DEVICE, "2026-06-14T09:00:00+00:00", "2026-06-14T09:10:00+00:00", 600, "break_taken"),
    )
    conn.commit()
    conn.close()

    result = get_todays_threshold(DEVICE, today="2026-06-15")
    assert result["threshold_seconds"] == result["baseline_seconds"], result
    assert result["profile"] == "Student"
    print(f"PASS: threshold stays at baseline after a healthy day ({result})")


# ---------- suggestions.py ----------

def test_suggestion_category_never_repeats_back_to_back():
    rotator = SuggestionRotator(rng=random.Random(42))
    seen = [rotator.next()["category"] for _ in range(50)]
    consecutive_repeats = sum(1 for i in range(1, len(seen)) if seen[i] == seen[i - 1])
    assert consecutive_repeats == 0, f"found {consecutive_repeats} back-to-back repeats in {seen}"
    print("PASS: suggestion category never repeats twice in a row, across 50 draws")


def test_all_categories_get_used_eventually():
    import suggestions as suggestions_module
    rotator = SuggestionRotator(rng=random.Random(7))
    seen = {rotator.next()["category"] for _ in range(50)}
    assert seen == set(suggestions_module.SUGGESTIONS.keys())
    print("PASS: all suggestion categories appear across enough draws")


def test_independent_rotators_do_not_share_state():
    r1 = SuggestionRotator(rng=random.Random(1))
    r2 = SuggestionRotator(rng=random.Random(1))
    first_from_each = [r1.next()["category"], r2.next()["category"]]
    assert first_from_each[0] == first_from_each[1], "same seed should give the same first pick"
    print("PASS: independently constructed rotators don't share hidden global state")


test_unknown_profile_falls_back_to_default()
test_setting_and_reading_active_profile_persists()
test_setting_invalid_profile_raises()
test_threshold_tightens_after_a_high_risk_day()
test_threshold_stays_at_baseline_after_a_good_day()
test_suggestion_category_never_repeats_back_to_back()
test_all_categories_get_used_eventually()
test_independent_rotators_do_not_share_state()
