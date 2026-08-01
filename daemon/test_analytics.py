"""Test analytics.py: session stats, daily trend, health timeline, reports, and export."""
import json
import tempfile
from datetime import date, timedelta
from pathlib import Path

import config
import db
import analytics

DEVICE = "test-device"


def fresh_test_db():
    config.DB_PATH = Path(tempfile.mkdtemp()) / "test_analytics.db"
    db.init_db()


def insert_session(duration_seconds, ended_reason, at_date):
    conn = db.get_connection()
    ts = f"{at_date}T10:00:00+00:00"
    conn.execute(
        "INSERT INTO sessions (device_id, start_time, end_time, duration_seconds, ended_reason) "
        "VALUES (?, ?, ?, ?, ?)",
        (DEVICE, ts, ts, duration_seconds, ended_reason),
    )
    conn.commit()
    conn.close()


def insert_event(event_type, at_date, at_time="10:00:00"):
    conn = db.get_connection()
    conn.execute(
        "INSERT INTO events (device_id, event_type, timestamp) VALUES (?, ?, ?)",
        (DEVICE, event_type, f"{at_date}T{at_time}+00:00"),
    )
    conn.commit()
    conn.close()


def test_session_stats_aggregate_correctly():
    fresh_test_db()
    insert_session(600, "break_taken", "2026-06-10")
    insert_session(1800, "went_idle", "2026-06-11")   # > threshold (1200), missed break
    insert_session(300, "break_taken", "2026-06-12")

    stats = analytics.get_session_stats(DEVICE, "2026-06-10", "2026-06-12")
    assert stats["total_sessions"] == 3
    assert stats["healthy_sessions"] == 2   # the two under 1200s
    assert stats["missed_break_sessions"] == 1
    assert stats["sessions_ended_by_break"] == 2
    assert stats["sessions_ended_by_idle"] == 1
    print(f"PASS: session stats aggregate correctly ({stats})")


def test_daily_trend_covers_every_day_in_range():
    fresh_test_db()
    insert_session(600, "break_taken", "2026-06-10")
    # no data at all for 06-11 or 06-12 — trend should still include those days

    trend = analytics.get_daily_trend(DEVICE, "2026-06-10", "2026-06-12")
    assert [t["date"] for t in trend] == ["2026-06-10", "2026-06-11", "2026-06-12"]
    assert trend[1]["score"] == 100  # empty day defaults clean, per Day 7's design
    print(f"PASS: daily trend covers every day, including ones with no data ({trend})")


def test_health_timeline_merges_events_and_healthy_sessions_in_order():
    fresh_test_db()
    insert_event("break_triggered", "2026-06-10", "09:00:00")
    insert_session(600, "break_taken", "2026-06-10")  # logged at 10:00:00 by insert_session's default
    insert_event("break_completed", "2026-06-10", "11:00:00")

    timeline = analytics.get_health_timeline(DEVICE, "2026-06-10", "2026-06-10")
    events_in_order = [e["event"] for e in timeline]
    assert events_in_order == ["break_triggered", "healthy_session_completed", "break_completed"], events_in_order
    print(f"PASS: health timeline merges events and healthy sessions in chronological order")


def test_unhealthy_session_does_not_appear_as_healthy_in_timeline():
    fresh_test_db()
    insert_session(1800, "went_idle", "2026-06-10")  # over threshold — should NOT show as "healthy"

    timeline = analytics.get_health_timeline(DEVICE, "2026-06-10", "2026-06-10")
    assert timeline == [], f"an over-threshold session should not appear as a healthy-session timeline entry, got {timeline}"
    print("PASS: an unhealthy (over-threshold) session doesn't show up as a healthy-session timeline entry")


def test_weekly_report_shape_and_average():
    fresh_test_db()
    today = date.today()
    insert_session(600, "break_taken", today.isoformat())
    insert_session(600, "break_taken", (today - timedelta(days=1)).isoformat())

    report = analytics.generate_report(DEVICE, days=7)
    assert len(report["daily_trend"]) == 7
    assert report["period_end"] == today.isoformat()
    assert report["average_wellness_score"] == 100  # both real days were healthy, empty days default to 100 too
    print(f"PASS: weekly report has 7 days and a correct average (avg={report['average_wellness_score']})")


def test_json_export_round_trips():
    fresh_test_db()
    insert_session(600, "break_taken", date.today().isoformat())
    report = analytics.generate_report(DEVICE, days=7)

    exported = analytics.export_report_json(report)
    parsed = json.loads(exported)
    assert parsed["average_wellness_score"] == report["average_wellness_score"]
    assert len(parsed["daily_trend"]) == 7
    print("PASS: JSON export round-trips back to the same data")


def test_csv_export_has_one_row_per_day_plus_header():
    fresh_test_db()
    insert_session(600, "break_taken", date.today().isoformat())
    report = analytics.generate_report(DEVICE, days=7)

    csv_text = analytics.export_report_csv(report)
    lines = [l for l in csv_text.strip().split("\r\n") if l]
    assert lines[0].startswith("date,wellness_score,fatigue_risk")
    assert len(lines) == 8, f"expected 1 header + 7 day rows, got {len(lines)} lines"
    print("PASS: CSV export has the expected header and one row per day")


test_session_stats_aggregate_correctly()
test_daily_trend_covers_every_day_in_range()
test_health_timeline_merges_events_and_healthy_sessions_in_order()
test_unhealthy_session_does_not_appear_as_healthy_in_timeline()
test_weekly_report_shape_and_average()
test_json_export_round_trips()
test_csv_export_has_one_row_per_day_plus_header()
