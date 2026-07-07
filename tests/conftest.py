# tests/conftest.py
# Shared pytest fixtures available to all test files in this directory.
# Emulators are started once per session to avoid port conflicts.

import socket
import threading
import time
import pytest
from datetime import datetime

from ammeters                   import EMULATOR_CLASSES
from src.testing.ammeter_tester import AmmeterTester
from src.testing.test_framework import AmmeterTestFramework
from src.utils.config           import load_config, get_config

# ── pytest hooks ────────────────────────────────────────────────────

def pytest_configure(config: pytest.Config) -> None:
    """
    Attach a timestamped FileHandler to the root logger so every TestLogger
    message (propagate=True) is captured in one unified per-session log file.
    Log level is read from config.yaml — change it there to affect all loggers.
    """
    import logging
    import os
    from src.utils.config import load_config

    cfg = get_config()
    level = getattr(logging, cfg["logging"]["level"], logging.INFO)

    os.makedirs("results/logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Use pipeline log file if set by run_pipeline.sh — single file for all stages
    log_path = os.environ.get("PYTEST_LOG_FILE") or f"results/logs/{timestamp}_pytest_run.log"

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(level)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """
    Automatically log every test result to the unified pipeline log.
    No need to add logger.info() to each test manually.
    """
    import logging
    if report.when == "call":
        # Extract test file name as logger name (e.g. tests/test_smoke.py -> test_smoke)
        logger_name = report.nodeid.split("::")[0].replace("/", ".").replace(".py", "").split(".")[-1]
        logger = logging.getLogger(logger_name)
        if report.passed:
            logger.info(f"PASSED  {report.nodeid}")
        elif report.failed:
            logger.error(f"FAILED  {report.nodeid}")
        elif report.skipped:
            logger.warning(f"SKIPPED {report.nodeid}")


# ── constants ────────────────────────────────────────────────────────

_startup = get_config()["testing"]["startup"]
STARTUP_TIMEOUT_SECONDS = _startup["timeout_seconds"]
STARTUP_POLL_INTERVAL   = _startup["poll_interval"]


# ── helpers ──────────────────────────────────────────────────────────

def wait_for_port(host: str, port: int, timeout: float) -> bool:
    """Poll a TCP port until it accepts connections or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(STARTUP_POLL_INTERVAL)
    return False


def start_emulators():
    """Start all ammeter emulators from config — single source of truth."""
    cfg = get_config()
    for name, data in cfg["ammeters"].items():
        emulator = EMULATOR_CLASSES[name]
        port     = data["port"]
        threading.Thread(
            target=lambda e=emulator, p=port: e(p).start_server(),
            daemon=True
        ).start()


# ── session fixture — emulators ───────────────────────────────────────

@pytest.fixture(scope="session")
def live_framework():
    """
    Session-scoped fixture: starts emulators ONCE for the entire test session.
    Shared across test_smoke.py, test_functional.py, and test_e2e.py.
    Teardown is automatic — emulators are daemon threads.
    """
    # BEFORE — create framework first (loads config.yaml internally — single source of truth)
    framework = AmmeterTestFramework()

    # Build port map from framework config — no hardcoded ports
    emulator_ports = {
        name: data["port"]
        for name, data in framework.config["ammeters"].items()
    }

    start_emulators()

    for name, port in emulator_ports.items():
        ready = wait_for_port("127.0.0.1", port, STARTUP_TIMEOUT_SECONDS)
        if not ready:
            pytest.fail(
                f"Emulator '{name}' did not start on port {port} "
                f"within {STARTUP_TIMEOUT_SECONDS}s — possible port conflict or crash."
            )

    yield framework

    # AFTER — daemon threads shut down automatically with the session


# ── unit test fixtures ───────────────────────────────────────────────

@pytest.fixture
def tester():
    """Create a fresh AmmeterTester instance for each test."""
    return AmmeterTester()


@pytest.fixture
def sample_measurements():
    """Fixed measurements for deterministic statistics tests."""
    return [(1.0, 1000.0), (2.0, 1001.0), (3.0, 1002.0), (4.0, 1003.0)]


@pytest.fixture
def single_measurement():
    """Single measurement — used for edge cases like std=0."""
    return [(5.0, 1000.0)]


@pytest.fixture
def negative_measurements():
    """Measurements with negative values — valid physically in some contexts."""
    return [(-2.0, 1000.0), (-1.0, 1001.0), (0.0, 1002.0), (1.0, 1003.0)]