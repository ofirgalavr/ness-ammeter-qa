# tests/test_e2e.py
# End-to-end tests for the full ammeter testing pipeline.
# Starts real emulators, runs measurements, validates results.
# Marked with @pytest.mark.e2e — run separately from unit tests:
#   ./venv/bin/python3 -m pytest tests/ -v -m "not e2e"  # unit tests only
#   ./venv/bin/python3 -m pytest tests/ -v -m e2e         # E2E only

import json
import os
import socket
import threading
import time

import pytest

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from src.testing.test_framework import AmmeterTestFramework

# ── constants ────────────────────────────────────────────────────────

EMULATOR_PORTS = {
    "greenlee": 5000,
    "entes":    5001,
    "circutor": 5002,
}

STARTUP_TIMEOUT_SECONDS = 10   # max time to wait for emulators to be ready
STARTUP_POLL_INTERVAL   = 0.2  # how often to check if emulator is up


# ── helpers ──────────────────────────────────────────────────────────

def wait_for_port(host: str, port: int, timeout: float) -> bool:
    """
    Poll a TCP port until it accepts connections or timeout expires.
    Returns True if port is ready, False if timeout exceeded.
    """
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


# ── fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def live_framework():
    """
    Module-scoped fixture: starts emulators once for all E2E tests.
    Waits until all ports are ready before yielding the framework.
    Fails with a clear message if any emulator does not start in time.
    """
    start_emulators()

    # Wait for each emulator to be ready
    for name, port in EMULATOR_PORTS.items():
        ready = wait_for_port("127.0.0.1", port, STARTUP_TIMEOUT_SECONDS)
        if not ready:
            pytest.fail(
                f"Emulator '{name}' did not start on port {port} "
                f"within {STARTUP_TIMEOUT_SECONDS}s — possible port conflict or crash."
            )

    yield AmmeterTestFramework()


# ── E2E tests ─────────────────────────────────────────────────────────

@pytest.mark.e2e
class TestE2EFullPipeline:

    def test_greenlee_returns_correct_measurement_count(self, live_framework):
        """Greenlee must return exactly measurements_count measurements per config."""
        result = live_framework.run_test("greenlee")
        expected = live_framework.config["testing"]["sampling"]["measurements_count"]
        assert len(result["measurements"]) == expected

    def test_entes_returns_correct_measurement_count(self, live_framework):
        """ENTES must return exactly measurements_count measurements per config."""
        result = live_framework.run_test("entes")
        expected = live_framework.config["testing"]["sampling"]["measurements_count"]
        assert len(result["measurements"]) == expected

    def test_circutor_returns_correct_measurement_count(self, live_framework):
        """Circutor must return exactly measurements_count measurements per config."""
        result = live_framework.run_test("circutor")
        expected = live_framework.config["testing"]["sampling"]["measurements_count"]
        assert len(result["measurements"]) == expected

    def test_all_measurements_are_positive(self, live_framework):
        """All ammeter measurements must return positive current values."""
        for ammeter in ["greenlee", "entes", "circutor"]:
            result = live_framework.run_test(ammeter)
            for value, _ in result["measurements"]:
                assert value > 0, f"{ammeter} returned non-positive value: {value}"

    def test_mean_between_min_and_max(self, live_framework):
        """Mean must always be between min and max for all ammeters."""
        for ammeter in ["greenlee", "entes", "circutor"]:
            result = live_framework.run_test(ammeter)
            stats = result["statistics"]
            assert stats["min"] <= stats["mean"] <= stats["max"], (
                f"{ammeter}: mean={stats['mean']} not between "
                f"min={stats['min']} and max={stats['max']}"
            )

    def test_statistics_keys_present(self, live_framework):
        """Statistics dict must contain all required keys for all ammeters."""
        for ammeter in ["greenlee", "entes", "circutor"]:
            result = live_framework.run_test(ammeter)
            assert set(result["statistics"].keys()) == {"count", "mean", "median", "std", "min", "max"}

    def test_save_results_creates_valid_json(self, live_framework, tmp_path, monkeypatch):
        """save_results must create a valid JSON file with all required fields."""
        monkeypatch.chdir(tmp_path)

        results = {}
        for ammeter in ["greenlee", "entes", "circutor"]:
            results[ammeter] = live_framework.run_test(ammeter)

        path = live_framework.tester.save_results(results)

        assert os.path.exists(path), "Results file was not created"

        with open(path) as f:
            data = json.load(f)

        assert "run_id" in data
        assert "timestamp" in data
        assert "results" in data
        assert set(data["results"].keys()) == {"greenlee", "entes", "circutor"}

    def test_each_ammeter_result_has_measurements_and_statistics(self, live_framework):
        """Each ammeter result must contain measurements and statistics keys."""
        for ammeter in ["greenlee", "entes", "circutor"]:
            result = live_framework.run_test(ammeter)
            assert "measurements" in result, f"{ammeter} missing measurements"
            assert "statistics" in result,   f"{ammeter} missing statistics"


# ── communication error tests ─────────────────────────────────────────

@pytest.mark.e2e
class TestE2ECommunicationErrors:

    def test_wrong_port_raises_connection_error(self):
        """Connecting to a wrong port must raise ConnectionRefusedError."""
        from Ammeters.client import request_current_from_ammeter
        with pytest.raises(ConnectionRefusedError):
            request_current_from_ammeter(9999, b'MEASURE_GREENLEE -get_measurement')

    def test_unknown_ammeter_raises_value_error(self, live_framework):
        """Unknown ammeter type must raise ValueError even with live emulators."""
        with pytest.raises(ValueError):
            live_framework.run_test("unknown_device")


# ── communication error tests ─────────────────────────────────────────

@pytest.mark.e2e
class TestE2EDataIntegrity:

    def test_run_id_is_unique_between_runs(self, live_framework, tmp_path, monkeypatch):
        """Two consecutive runs must produce different run_ids."""
        monkeypatch.chdir(tmp_path)

        results = {
            "greenlee": live_framework.run_test("greenlee"),
            "entes":    live_framework.run_test("entes"),
            "circutor": live_framework.run_test("circutor"),
        }

        path1 = live_framework.tester.save_results(results)
        path2 = live_framework.tester.save_results(results)

        with open(path1) as f:
            data1 = json.load(f)
        with open(path2) as f:
            data2 = json.load(f)

        assert data1["run_id"] != data2["run_id"], "Two runs produced the same run_id"

    def test_json_roundtrip_preserves_data(self, live_framework, tmp_path, monkeypatch):
        """Data saved to JSON must be identical when loaded back."""
        monkeypatch.chdir(tmp_path)

        results = {
            "greenlee": live_framework.run_test("greenlee"),
            "entes":    live_framework.run_test("entes"),
            "circutor": live_framework.run_test("circutor"),
        }

        path = live_framework.tester.save_results(results)

        with open(path) as f:
            data = json.load(f)

        # Verify statistics are preserved exactly for all ammeters
        for ammeter in ["greenlee", "entes", "circutor"]:
            saved_stats = data["results"][ammeter]["statistics"]
            original_stats = results[ammeter]["statistics"]
            assert saved_stats == original_stats, (
                f"{ammeter} statistics changed after JSON roundtrip"
            )

        # Verify measurement count is preserved
        for ammeter in ["greenlee", "entes", "circutor"]:
            saved_count = len(data["results"][ammeter]["measurements"])
            original_count = len(results[ammeter]["measurements"])
            assert saved_count == original_count, (
                f"{ammeter} measurement count changed after JSON roundtrip"
            )
