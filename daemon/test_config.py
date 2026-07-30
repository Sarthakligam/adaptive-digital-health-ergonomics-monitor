"""
test_config.py

Basic tests for config.py.
Run:
    python3 test_config.py
"""

from pathlib import Path
import config


def check(condition, message):
    if condition:
        print(f"PASS: {message}")
    else:
        print(f"FAIL: {message}")
        raise AssertionError(message)


def test_data_directory():
    check(
        isinstance(config.DATA_DIR, Path),
        "DATA_DIR is a Path object"
    )

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    check(
        config.DATA_DIR.exists(),
        "DATA_DIR exists"
    )


def test_database_path():
    check(
        config.DB_PATH.name.endswith(".db"),
        "database filename is valid"
    )


def test_thresholds():
    check(
        config.IDLE_TIMEOUT_SECONDS > 0,
        "idle timeout is positive"
    )

    check(
        config.CONTINUOUS_THRESHOLD_SECONDS > 0,
        "continuous threshold is positive"
    )

    check(
        config.CHECK_INTERVAL_SECONDS > 0,
        "check interval is positive"
    )


def test_device_id():
    device1 = config.get_device_id()
    device2 = config.get_device_id()

    check(
        device1 == device2,
        "device ID persists across calls"
    )

    check(
        len(device1) > 0,
        "device ID is not empty"
    )


def test_logging():
    config.setup_logging()

    check(
        config.LOG_PATH.exists(),
        "log file created"
    )


if __name__ == "__main__":
    test_data_directory()
    test_database_path()
    test_thresholds()
    test_device_id()
    test_logging()

    print("\nAll config tests passed!")
