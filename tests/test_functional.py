# tests/test_functional.py
# Functional tests for the ammeter testing framework.
# Verifies features behave correctly from the user's perspective.
# Requires live emulators to run — started once via conftest.py session fixture.

import json
import pytest

from ammeters.client import request_current_from_ammeter


# ── measurement tests ─────────────────────────────────────────────────

@pytest.mark.functional
class TestFunctionalMeasurements:

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
            assert stats["min"] <= stats["mean"] <= stats["max"]

    def test_statistics_keys_present(self, live_framework):
        """Statistics dict must contain all required keys for all ammeters."""
        for ammeter in ["greenlee", "entes", "circutor"]:
            result = live_framework.run_test(ammeter)
            assert set(result["statistics"].keys()) == {"count", "mean", "median", "std", "min", "max"}

    def test_each_ammeter_result_has_measurements_and_statistics(self, live_framework):
        """Each ammeter result must contain measurements and statistics keys."""
        for ammeter in ["greenlee", "entes", "circutor"]:
            result = live_framework.run_test(ammeter)
            assert "measurements" in result, f"{ammeter} missing measurements"
            assert "statistics" in result,   f"{ammeter} missing statistics"


# ── data integrity tests ──────────────────────────────────────────────

@pytest.mark.functional
class TestFunctionalDataIntegrity:

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
        for ammeter in ["greenlee", "entes", "circutor"]:
            assert data["results"][ammeter]["statistics"] == results[ammeter]["statistics"]
            assert len(data["results"][ammeter]["measurements"]) == len(results[ammeter]["measurements"])


# ── error tests ───────────────────────────────────────────────────────

@pytest.mark.functional
class TestFunctionalErrors:

    def test_wrong_port_raises_connection_error(self):
        """Connecting to a wrong port must raise ConnectionRefusedError."""
        with pytest.raises(ConnectionRefusedError):
            request_current_from_ammeter(9999, b'MEASURE_GREENLEE -get_measurement')

    def test_unknown_ammeter_raises_value_error(self, live_framework):
        """Unknown ammeter type must raise ValueError even with live emulators."""
        with pytest.raises(ValueError):
            live_framework.run_test("unknown_device")