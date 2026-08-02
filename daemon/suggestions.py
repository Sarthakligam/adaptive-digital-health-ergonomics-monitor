"""
suggestions.py — Categorized ergonomic suggestions, rotated so the
same category never repeats twice in a row (the "intelligent" part —
simple and fully deterministic given a seeded random source, so it's
testable).
"""

import random

SUGGESTIONS = {
    "Eye Care": [
        "Look at something 20 feet away for 20 seconds (the 20-20-20 rule).",
        "Blink deliberately several times to re-wet your eyes.",
        "Adjust your screen brightness to match the room around you.",
    ],
    "Neck & Shoulder": [
        "Slowly roll your shoulders backward, 5 times.",
        "Gently tilt your head ear-to-shoulder on each side.",
        "Interlace your fingers and stretch your arms overhead.",
    ],
    "Hydration": [
        "Drink a glass of water.",
        "Refill your water bottle before you sit back down.",
    ],
    "Movement": [
        "Stand up and walk for two minutes.",
        "Do 10 bodyweight squats.",
        "Take a short walk, even just to another room.",
    ],
    "Posture": [
        "Check your posture — feet flat, back supported.",
        "Adjust your chair or screen so the top of the screen is at eye level.",
    ],
    "Mental Refresh": [
        "Close your eyes and take five slow breaths.",
        "Step away from your screen and look out a window.",
    ],
}


class SuggestionRotator:
    """A class (not module globals) so tests can create independent,
    isolated rotators instead of sharing hidden mutable state."""

    def __init__(self, rng: random.Random = None):
        self._rng = rng or random.Random()
        self._last_category = None

    def next(self) -> dict:
        candidates = [c for c in SUGGESTIONS if c != self._last_category] or list(SUGGESTIONS)
        category = self._rng.choice(candidates)
        self._last_category = category
        text = self._rng.choice(SUGGESTIONS[category])
        return {"category": category, "suggestion": text}


_default_rotator = SuggestionRotator()


def get_next_suggestion() -> dict:
    return _default_rotator.next()
