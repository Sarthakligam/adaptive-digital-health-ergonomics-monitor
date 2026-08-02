"""Test config.py's device_id persistence and .env loader, in isolated temp dirs."""
import os
import tempfile
from pathlib import Path

import config


def test_device_id_persists_across_calls():
    config.DATA_DIR = Path(tempfile.mkdtemp())
    first = config.get_device_id()
    second = config.get_device_id()
    assert first == second, f"device_id should be stable across calls, got {first} != {second}"
    assert len(first) == 36, f"expected a UUID string, got {first!r}"
    print("PASS: device_id persists across calls")


def test_device_id_differs_per_fresh_install():
    config.DATA_DIR = Path(tempfile.mkdtemp())
    id_a = config.get_device_id()
    config.DATA_DIR = Path(tempfile.mkdtemp())  # simulate a different machine
    id_b = config.get_device_id()
    assert id_a != id_b, "two different installs should not collide on the same device_id"
    print("PASS: fresh installs get distinct device_ids")


def test_dotenv_loader_sets_environment_variables():
    tmp_dir = tempfile.mkdtemp()
    env_path = Path(tmp_dir) / ".env"
    env_path.write_text("ADHEM_TEST_KEY=hello\n# a comment\n\nADHEM_TEST_KEY2=world\n")
    os.environ.pop("ADHEM_TEST_KEY", None)
    os.environ.pop("ADHEM_TEST_KEY2", None)
    config._load_dotenv(str(env_path))
    assert os.environ.get("ADHEM_TEST_KEY") == "hello"
    assert os.environ.get("ADHEM_TEST_KEY2") == "world"
    print("PASS: .env loader sets environment variables, skips comments/blank lines")


def test_dotenv_loader_is_safe_when_file_missing():
    config._load_dotenv("/tmp/definitely-does-not-exist/.env")
    print("PASS: missing .env file doesn't raise")


def test_setup_logging_does_not_crash():
    config.DATA_DIR = Path(tempfile.mkdtemp())
    config.LOG_PATH = config.DATA_DIR / "test.log"
    config.setup_logging()
    assert config.LOG_PATH.exists(), "expected the log file to be created"
    print("PASS: setup_logging runs without error and creates the log file")


test_device_id_persists_across_calls()
test_device_id_differs_per_fresh_install()
test_dotenv_loader_sets_environment_variables()
test_dotenv_loader_is_safe_when_file_missing()
test_setup_logging_does_not_crash()
