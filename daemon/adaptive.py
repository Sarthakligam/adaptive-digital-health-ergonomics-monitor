"""
adaptive.py — Adjusts today's continuous-use threshold based on how
yesterday actually went. Deliberately a simple, stated heuristic
rather than a model — see docs/ARCHITECTURE.md's "AI-ready, not AI
now" reasoning. If yesterday's fatigue risk was High, today's
threshold tightens (reminds sooner); otherwise it stays at the
active profile's baseline.
"""

from datetime import date, timedelta

from profiles import get_profile, get_active_profile_key
from wellness import compute_daily_wellness

TIGHTEN_FACTOR = 0.75  # 25% shorter than baseline when yesterday was High risk


def get_todays_threshold(device_id: str, today: str = None) -> dict:
    """
    Returns a dict (not just a number) so the reasoning is inspectable —
    an "adaptive" number with no explanation would fail the same
    explainability bar the wellness score is held to.
    """
    profile = get_profile(get_active_profile_key())
    baseline = profile.continuous_threshold_seconds

    if today is None:
        today = date.today().isoformat()
    yesterday = (date.fromisoformat(today) - timedelta(days=1)).isoformat()

    yesterday_result = compute_daily_wellness(device_id, yesterday)

    if yesterday_result.fatigue_risk == "High":
        threshold = round(baseline * TIGHTEN_FACTOR)
        reason = f"Tightened — yesterday's fatigue risk was High (score {yesterday_result.score})"
    else:
        threshold = baseline
        reason = f"Using {profile.display_name} baseline — yesterday's risk was {yesterday_result.fatigue_risk}"

    return {
        "threshold_seconds": threshold,
        "baseline_seconds": baseline,
        "profile": profile.display_name,
        "reason": reason,
    }
