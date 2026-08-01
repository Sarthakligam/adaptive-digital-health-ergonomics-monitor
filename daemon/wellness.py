"""
wellness.py — Digital Wellness Score, Fatigue Risk Indicator, and Daily
Wellness Goal progress, computed from the sessions/events tables.

Deliberately built as explainable, hand-written heuristics rather than
a black-box model — every point lost or kept has a stated reason (see
docs/ARCHITECTURE.md for why: this keeps the score defensible in a
viva, and the inputs stay clean numeric data an actual model could
consume later, without needing AI to explain today's number).
"""

from dataclasses import dataclass, field
from datetime import date as date_cls
from typing import List

import config
from db import get_connection


@dataclass
class WellnessResult:
    date: str
    score: int
    fatigue_risk: str  # "Low" | "Moderate" | "High"
    reasons: List[str] = field(default_factory=list)
    healthy_breaks: int = 0
    daily_goal: int = 0
    longest_session_seconds: int = 0
    average_session_seconds: int = 0


def _sessions_for_date(device_id: str, target_date: str):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT duration_seconds, ended_reason FROM sessions "
            "WHERE device_id = ? AND DATE(end_time) = ?",
            (device_id, target_date),
        ).fetchall()
    finally:
        conn.close()


def _break_event_counts(device_id: str, target_date: str) -> dict:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT event_type, COUNT(*) as n FROM events "
            "WHERE device_id = ? AND DATE(timestamp) = ? "
            "AND event_type IN ('break_triggered', 'break_completed', 'break_snoozed') "
            "GROUP BY event_type",
            (device_id, target_date),
        ).fetchall()
        return {r["event_type"]: r["n"] for r in rows}
    finally:
        conn.close()


def compute_daily_wellness(device_id: str, target_date: str = None) -> WellnessResult:
    """
    Compute the wellness score for one device on one day (defaults to
    today). Starts at 100 and deducts points for specific, named
    reasons — never a mystery drop.
    """
    if target_date is None:
        target_date = date_cls.today().isoformat()

    sessions = _sessions_for_date(device_id, target_date)
    events = _break_event_counts(device_id, target_date)
    threshold = config.CONTINUOUS_THRESHOLD_SECONDS

    score = 100
    reasons: List[str] = []

    durations = [s["duration_seconds"] for s in sessions]
    long_sessions = [d for d in durations if d > threshold]

    if durations and not long_sessions:
        reasons.append("Healthy average session length")

    for d in long_sessions:
        overshoot_ratio = (d - threshold) / threshold
        score -= min(20, overshoot_ratio * 15)

    if len(long_sessions) == 1:
        reasons.append("One prolonged session")
    elif len(long_sessions) > 1:
        reasons.append(f"{len(long_sessions)} prolonged sessions")

    very_long = [d for d in long_sessions if d > threshold * 2]
    if very_long:
        score -= 10

    breaks_triggered = events.get("break_triggered", 0)
    breaks_completed = events.get("break_completed", 0)
    breaks_snoozed = events.get("break_snoozed", 0)
    if breaks_triggered > 0:
        compliance = breaks_completed / breaks_triggered
        if compliance < 0.5:
            score -= 15
            reasons.append(f"{breaks_snoozed} missed/snoozed break(s)")
        elif breaks_snoozed == 0:
            reasons.append("Good break compliance")

    healthy_break_sessions = sum(1 for s in sessions if s["ended_reason"] == "break_taken")
    idle_sessions = sum(1 for s in sessions if s["ended_reason"] == "went_idle")
    if healthy_break_sessions > 0 and idle_sessions > 0:
        reasons.append("Good idle/break balance")

    score = max(0, min(100, round(score)))

    if score >= 80:
        fatigue_risk = "Low"
    elif score >= 50:
        fatigue_risk = "Moderate"
    else:
        fatigue_risk = "High"

    return WellnessResult(
        date=target_date,
        score=score,
        fatigue_risk=fatigue_risk,
        reasons=reasons or ["No significant activity recorded"],
        healthy_breaks=healthy_break_sessions,
        daily_goal=config.DAILY_BREAK_GOAL,
        longest_session_seconds=max(durations, default=0),
        average_session_seconds=round(sum(durations) / len(durations)) if durations else 0,
    )
