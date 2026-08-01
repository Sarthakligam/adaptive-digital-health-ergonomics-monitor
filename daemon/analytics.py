"""
analytics.py — Session statistics, trends, the Health Timeline, and
weekly/monthly reports (with CSV/JSON export). Built on the same
sessions/events tables the wellness engine (Day 7) reads, and reuses
compute_daily_wellness() rather than duplicating its scoring logic.
"""

import csv
import io
import json
from datetime import date as date_cls, timedelta
from typing import Dict, List

import config
from db import get_connection
from wellness import compute_daily_wellness


def get_session_stats(device_id: str, start_date: str, end_date: str) -> Dict:
    """Aggregate session stats over an inclusive date range (by end_time's date)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT duration_seconds, ended_reason FROM sessions "
            "WHERE device_id = ? AND DATE(end_time) BETWEEN ? AND ?",
            (device_id, start_date, end_date),
        ).fetchall()
    finally:
        conn.close()

    threshold = config.CONTINUOUS_THRESHOLD_SECONDS
    durations = [r["duration_seconds"] for r in rows]
    healthy = [d for d in durations if d <= threshold]
    missed = sum(1 for r in rows if r["ended_reason"] == "went_idle" and r["duration_seconds"] > threshold)

    return {
        "total_sessions": len(durations),
        "average_session_seconds": round(sum(durations) / len(durations)) if durations else 0,
        "longest_session_seconds": max(durations, default=0),
        "healthy_sessions": len(healthy),
        "sessions_ended_by_break": sum(1 for r in rows if r["ended_reason"] == "break_taken"),
        "sessions_ended_by_idle": sum(1 for r in rows if r["ended_reason"] == "went_idle"),
        "missed_break_sessions": missed,
    }


def get_daily_trend(device_id: str, start_date: str, end_date: str) -> List[Dict]:
    """
    One wellness score per calendar day in the range. Reuses Day 7's
    tested compute_daily_wellness() per day rather than re-implementing
    the scoring logic here — a known tradeoff (N queries instead of one
    aggregate query) that's fine at this project's scale; worth noting
    as an optimization opportunity if data volume ever grows.
    """
    start = date_cls.fromisoformat(start_date)
    end = date_cls.fromisoformat(end_date)
    trend = []
    d = start
    while d <= end:
        result = compute_daily_wellness(device_id, d.isoformat())
        trend.append({"date": d.isoformat(), "score": result.score, "fatigue_risk": result.fatigue_risk})
        d += timedelta(days=1)
    return trend


def get_health_timeline(device_id: str, start_date: str, end_date: str) -> List[Dict]:
    """
    Chronological list of wellness-relevant moments: break
    triggered/completed/snoozed, went idle (from events), plus
    synthesized "healthy_session_completed" entries for sessions that
    ended on their own without ever exceeding the threshold.
    """
    conn = get_connection()
    try:
        event_rows = conn.execute(
            "SELECT event_type, timestamp FROM events "
            "WHERE device_id = ? AND DATE(timestamp) BETWEEN ? AND ? "
            "AND event_type IN ('break_triggered','break_completed','break_snoozed','went_idle')",
            (device_id, start_date, end_date),
        ).fetchall()
        session_rows = conn.execute(
            "SELECT end_time, duration_seconds FROM sessions "
            "WHERE device_id = ? AND DATE(end_time) BETWEEN ? AND ? AND duration_seconds <= ?",
            (device_id, start_date, end_date, config.CONTINUOUS_THRESHOLD_SECONDS),
        ).fetchall()
    finally:
        conn.close()

    timeline = [{"timestamp": r["timestamp"], "event": r["event_type"]} for r in event_rows]
    timeline += [{"timestamp": r["end_time"], "event": "healthy_session_completed"} for r in session_rows]
    timeline.sort(key=lambda e: e["timestamp"])
    return timeline


def generate_report(device_id: str, days: int) -> Dict:
    """days=7 for a weekly report, days=30 for monthly."""
    end = date_cls.today()
    start = end - timedelta(days=days - 1)
    trend = get_daily_trend(device_id, start.isoformat(), end.isoformat())
    stats = get_session_stats(device_id, start.isoformat(), end.isoformat())
    scores = [t["score"] for t in trend]
    return {
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "average_wellness_score": round(sum(scores) / len(scores)) if scores else 0,
        "daily_trend": trend,
        "session_stats": stats,
    }


def export_report_json(report: Dict) -> str:
    return json.dumps(report, indent=2)


def export_report_csv(report: Dict) -> str:
    """Flat, spreadsheet-friendly CSV — one row per day in the trend, stats repeated as context columns."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "wellness_score", "fatigue_risk", "period_average_score", "total_sessions_in_period"])
    for row in report["daily_trend"]:
        writer.writerow([
            row["date"], row["score"], row["fatigue_risk"],
            report["average_wellness_score"], report["session_stats"]["total_sessions"],
        ])
    return buf.getvalue()
