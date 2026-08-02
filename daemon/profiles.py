"""
profiles.py — Configurable Wellness Profiles.

Each profile is a baseline continuous-use threshold suited to a kind
of work. The chosen profile is the *baseline* that adaptive.py then
adjusts day to day based on how yesterday actually went.
"""

from dataclasses import dataclass

import config


@dataclass(frozen=True)
class WellnessProfile:
    key: str
    display_name: str
    continuous_threshold_seconds: int
    idle_timeout_seconds: int
    description: str


PROFILES = {
    "student": WellnessProfile(
        "student", "Student", 25 * 60, 5 * 60,
        "Longer focus blocks for study sessions, standard break sensitivity.",
    ),
    "developer": WellnessProfile(
        "developer", "Developer", 20 * 60, 5 * 60,
        "Balanced for deep-focus coding work — the project's default.",
    ),
    "designer": WellnessProfile(
        "designer", "Designer", 20 * 60, 4 * 60,
        "Shorter idle window — frequent switching between tools counts as activity.",
    ),
    "office_employee": WellnessProfile(
        "office_employee", "Office Employee", 15 * 60, 5 * 60,
        "Shorter continuous blocks — frequent context switching between tasks/meetings.",
    ),
}

DEFAULT_PROFILE_KEY = "developer"


def get_profile(key: str) -> WellnessProfile:
    """Unknown or missing key safely falls back to the default profile."""
    return PROFILES.get(key, PROFILES[DEFAULT_PROFILE_KEY])


def _profile_file():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return config.DATA_DIR / "profile"


def get_active_profile_key() -> str:
    f = _profile_file()
    if f.exists():
        key = f.read_text().strip()
        if key in PROFILES:
            return key
    return DEFAULT_PROFILE_KEY


def set_active_profile(key: str) -> WellnessProfile:
    if key not in PROFILES:
        raise ValueError(f"Unknown profile: {key!r}. Valid options: {list(PROFILES)}")
    _profile_file().write_text(key)
    return PROFILES[key]
