# tests/conftest.py
# Shared pytest fixtures available to all test files in this directory.
# Emulators are started once per session to avoid port conflicts.

import socket
import threading
import time
import pytest
from datetime import datetime

from ammeters.circutor_ammeter import CircutorAmmeter
from ammeters.entes_ammeter import EntesAmmeter
from ammeters.greenlee_ammeter import GreenleeAmmeter
from src.testing.ammeter_tester import AmmeterTester
from src.testing.test_framework import AmmeterTestFramework

# ── pytest hooks ────────────────────────────────────────────────────

def pytest_configure(config: pytest.Config) -> None:
    """
    Attach a timestamped FileHandler to the root logger so every TestLogger
    message (propagate=True) is captured in one unified per-session log file.
    """
    import logging
    import os
    os.makedirs("results/logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"results/logs/{timestamp}_pytest_run.log"

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


# ── constants ────────────────────────────────────────────────────────

EMULATOR_PORTS = {
    "greenlee": 5000,
    "entes":    5001,
    "circutor": 5002,
}

STARTUP_TIMEOUT_SECONDS = 10
STARTUP_POLL_INTERVAL   = 0.2


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
    """Start all three ammeter emulators in background daemon threads."""
    threading.Thread(target=lambda: GreenleeAmmeter(5000).start_server(), daemon=True).start()
    threading.Thread(target=lambda: EntesAmmeter(5001).start_server(),    daemon=True).start()
    threading.Thread(target=lambda: CircutorAmmeter(5002).start_server(), daemon=True).start()


# ── session fixture — emulators ───────────────────────────────────────

@pytest.fixture(scope="session")
def live_framework():
    """
    Session-scoped fixture: starts emulators ONCE for the entire test session.
    Shared across test_smoke.py, test_functional.py, and test_e2e.py.
    Teardown is automatic — emulators are daemon threads.
    """
    # BEFORE — start emulators and wait for them to be ready
    start_emulators()

    for name, port in EMULATOR_PORTS.items():
        ready = wait_for_port("127.0.0.1", port, STARTUP_TIMEOUT_SECONDS)
        if not ready:
            pytest.fail(
                f"Emulator '{name}' did not start on port {port} "
                f"within {STARTUP_TIMEOUT_SECONDS}s — possible port conflict or crash."
            )

    yield AmmeterTestFramework()

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