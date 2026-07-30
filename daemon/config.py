"""
config.py — Centralized configuration for ADHEM.

Everything that used to be a hardcoded constant scattered across
files (DB path, thresholds, ports) lives here instead, read from
environment variables with sensible defaults. This is what makes
dev/test/prod environments possible later: change the environment
variables, not the code.
"""

import logging
import os
import uuid
from pathlib import Path


def _load_dotenv(path: str = ".env") -> None:
    """
    Minimal .env file loader: reads KEY=VALUE lines into os.environ.
    Real-world projects often reach for the `python-dotenv` package for
    this — this hand-rolled version avoids adding a dependency for
    something this small, and keeps the mechanism fully visible. Safe
    to call even if the file doesn't exist (does nothing).
    """
    env_file = Path(path)
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

ENVIRONMENT = os.getenv("ADHEM_ENV", "development")  # development | testing | production

DATA_DIR = Path(os.getenv("ADHEM_DATA_DIR", str(Path.home() / ".adhem")))
DB_PATH = DATA_DIR / os.getenv("ADHEM_DB_NAME", "adhem.db")
LOG_PATH = DATA_DIR / "adhem.log"

IDLE_TIMEOUT_SECONDS = int(os.getenv("ADHEM_IDLE_TIMEOUT", str(5 * 60)))
CONTINUOUS_THRESHOLD_SECONDS = int(os.getenv("ADHEM_CONTINUOUS_THRESHOLD", str(20 * 60)))
CHECK_INTERVAL_SECONDS = int(os.getenv("ADHEM_CHECK_INTERVAL", "5"))
SNOOZE_GRACE_SECONDS = int(os.getenv("ADHEM_SNOOZE_GRACE", str(5 * 60)))

WS_HOST = os.getenv("ADHEM_WS_HOST", "0.0.0.0")
WS_PORT = int(os.getenv("ADHEM_WS_PORT", "8000"))

LOG_LEVEL = os.getenv("ADHEM_LOG_LEVEL", "INFO")


def get_device_id() -> str:
    """
    Returns a UUID that's generated once per installation and persisted
    to disk, so the same device always reports the same device_id —
    this is what lets the future cloud sync tell multiple devices'
    data apart in the same database.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    device_id_file = DATA_DIR / "device_id"
    if device_id_file.exists():
        return device_id_file.read_text().strip()
    new_id = str(uuid.uuid4())
    device_id_file.write_text(new_id)
    return new_id


DEVICE_ID = get_device_id()

_logging_configured = False


def setup_logging() -> None:
    """Configure logging once for the whole process: console + a log file, with levels."""
    global _logging_configured
    if _logging_configured:
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler(),
        ],
    )
    _logging_configured = True
