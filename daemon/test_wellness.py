"""Test wellness.py's score/fatigue-risk/goal computation with synthetic session/event data."""
import tempfile
from pathlib import Path

import config
import db
from wellness import compute_daily_wellness

TEST_DATE = "2026-06-15"
DEVICE = "test-device"


def fresh_test_db():
    config.DB_PATH = Path(tempfile.mkdtemp()) / "test_wellness.db"
    db.init_db()


def insert_session(duration_seconds, ended_reason, at_time=f"{TEST_DATE}T10:00:00+00:00"):
    conn = db.get_connection()
    conn.execute(
        "INSERT INTO sessions (device_id, start_time, end_time, duration_seconds, ended_reason) "
        "VALUES (?, ?, ?, ?, ?)",
        (DEVICE, at_time, at_time, duration_seconds, ended_reason),
    )
    conn.commit()
    conn.close()


def insert_event(event_type, at_time=f"{TEST_DATE}T10:00:00+00:00"):
    conn = db.get_connection()
    conn.execute(
        "INSERT INTO events (device_id, event_type, timestamp) VALUES (?, ?, ?)",
        (DEVICE, event_type, at_time),
    )
    conn.commit()
    conn.close()


def test_perfect_day_scores_high_and_low_risk():
    fresh_test_db()
    insert_session(600, "break_taken")   # 10 min, under the 20-min threshold
    insert_session(900, "break_taken")   # 15 min
    insert_event("break_triggered")
    insert_event("break_completed")

    result = compute_daily_wellness(DEVICE, TEST_DATE)
    assert result.score >= 90, f"expected a high score for a healthy day, got {result.score}"
    assert result.fatigue_risk == "Low", f"expected Low risk, got {result.fatigue_risk}"
    assert "Healthy average session length" in result.reasons
    print(f"PASS: perfect day scores high and Low risk (score={result.score})")


def test_one_prolonged_session_reduces_score_and_explains_why():
    fresh_test_db()
    insert_session(2700, "went_idle")  # 45 min, well over the 20-min threshold

    result = compute_daily_wellness(DEVICE, TEST_DATE)
    assert result.score < 100, f"expected a reduced score, got {result.score}"
    assert any("prolonged session" in r for r in result.reasons), result.reasons
    print(f"PASS: one prolonged session reduces score with a stated reason (score={result.score})")


def test_missed_breaks_reduce_score_and_explain_why():
    fresh_test_db()
    insert_session(600, "break_taken")
    for _ in range(4):
        insert_event("break_triggered")
    insert_event("break_completed")  # only 1 of 4 triggered breaks actually completed
    for _ in range(3):
        insert_event("break_snoozed")

    result = compute_daily_wellness(DEVICE, TEST_DATE)
    assert any("missed/snoozed" in r for r in result.reasons), result.reasons
    print(f"PASS: low break compliance reduces score with a stated reason (score={result.score})")


def test_very_long_session_pushes_into_high_risk():
    fresh_test_db()
    insert_session(5000, "went_idle")  # ~83 min, more than 4x the 20-min threshold
    for _ in range(3):
        insert_event("break_triggered")
    for _ in range(3):
        insert_event("break_snoozed")

    result = compute_daily_wellness(DEVICE, TEST_DATE)
    assert result.fatigue_risk in ("Moderate", "High"), f"expected elevated risk, got {result.fatigue_risk}"
    print(f"PASS: a very long unbroken session pushes fatigue risk up (score={result.score}, risk={result.fatigue_risk})")


def test_no_activity_defaults_to_a_clean_result():
    fresh_test_db()
    result = compute_daily_wellness(DEVICE, TEST_DATE)
    assert result.score == 100
    assert result.fatigue_risk == "Low"
    assert result.reasons == ["No significant activity recorded"]
    print("PASS: a day with no recorded activity doesn't get penalized")


def test_daily_goal_progress_counts_only_real_breaks():
    fresh_test_db()
    insert_session(600, "break_taken")
    insert_session(700, "break_taken")
    insert_session(400, "went_idle")  # should NOT count toward the goal

    result = compute_daily_wellness(DEVICE, TEST_DATE)
    assert result.healthy_breaks == 2, f"expected 2 healthy breaks, got {result.healthy_breaks}"
    assert result.daily_goal == config.DAILY_BREAK_GOAL
    print(f"PASS: daily goal progress counts only real breaks ({result.healthy_breaks}/{result.daily_goal})")


test_perfect_day_scores_high_and_low_risk()
test_one_prolonged_session_reduces_score_and_explains_why()
test_missed_breaks_reduce_score_and_explain_why()
test_very_long_session_pushes_into_high_risk()
test_no_activity_defaults_to_a_clean_result()
test_daily_goal_progress_counts_only_real_breaks()
