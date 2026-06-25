# tests/test_ammeter_tester.py
# Unit tests for AmmeterTester — validations and core logic.
# Uses unittest.mock to avoid requiring live ammeter servers.

import pytest
import json
import os

from unittest.mock import patch
from src.testing.ammeter_tester import AmmeterTester


# ── calculate_statistics ────────────────────────────────────────────

@pytest.mark.unit
class TestCalculateStatistics:

    def test_empty_list_raises(self, tester):
        """Empty measurements list must raise ValueError."""
        with pytest.raises(ValueError):
            tester.calculate_statistics([])

    def test_single_measurement_std_is_zero(self, tester):
        """Single measurement should return std=0.0."""
        result = tester.calculate_statistics([(5.0, 1000.0)])
        assert result["std"] == 0.0

    def test_mean_between_min_and_max(self, tester, sample_measurements):
        """Mean must always be between min and max."""
        result = tester.calculate_statistics(sample_measurements)
        assert result["min"] <= result["mean"] <= result["max"]

    def test_known_values(self, tester, sample_measurements):
        """Verify statistics on known input [1,2,3,4]."""
        result = tester.calculate_statistics(sample_measurements)
        assert result["count"] == 4
        assert result["mean"] == 2.5
        assert result["median"] == 2.5
        assert result["min"] == 1.0
        assert result["max"] == 4.0


# ── sample ──────────────────────────────────────────────────────────

@pytest.mark.unit
class TestSample:

    def test_unknown_ammeter_raises(self, tester):
        """Unknown ammeter type must raise ValueError."""
        with pytest.raises(ValueError):
            tester.sample("unknown", 4, 10, 0.5)

    def test_negative_num_measurements_raises(self, tester):
        """Non-positive num_measurements must raise ValueError."""
        with pytest.raises(ValueError):
            tester.sample("greenlee", -1, 10, 0.5)

    def test_negative_duration_raises(self, tester):
        """Non-positive duration must raise ValueError."""
        with pytest.raises(ValueError):
            tester.sample("greenlee", 4, -5, 0.5)

    def test_negative_frequency_raises(self, tester):
        """Non-positive frequency must raise ValueError."""
        with pytest.raises(ValueError):
            tester.sample("greenlee", 4, 10, -1)

    def test_inconsistent_params_raises(self, tester):
        """num_measurements > duration * frequency must raise ValueError."""
        with pytest.raises(ValueError):
            tester.sample("greenlee", 100, 10, 0.5)

    @patch("src.testing.ammeter_tester.client.request_current_from_ammeter")
    def test_successful_sample_returns_correct_length(self, mock_client, tester):
        """Successful sample must return list with num_measurements items."""
        mock_client.return_value = (1.5, 1000.0)
        results = tester.sample("greenlee", 3, 10, 1.0)
        assert len(results) == 3

    @patch("src.testing.ammeter_tester.client.request_current_from_ammeter")
    def test_successful_sample_returns_tuples(self, mock_client, tester):
        """Each measurement must be a tuple of (float, float)."""
        mock_client.return_value = (2.0, 9999.0)
        results = tester.sample("greenlee", 2, 10, 1.0)
        assert all(isinstance(m, tuple) and len(m) == 2 for m in results)


# ── save_results ────────────────────────────────────────────────────

@pytest.mark.unit
class TestSaveResults:

    def test_empty_results_raises(self, tester):
        """Empty results dict must raise ValueError."""
        with pytest.raises(ValueError):
            tester.save_results({})

    def test_file_is_created(self, tester, sample_measurements, tmp_path, monkeypatch):
        """save_results must create a JSON file in the results directory."""
        monkeypatch.chdir(tmp_path)
        results = {
            "greenlee": {
                "measurements": sample_measurements,
                "statistics": tester.calculate_statistics(sample_measurements),
            }
        }
        path = tester.save_results(results)
        assert os.path.exists(path)

    def test_file_contains_required_fields(self, tester, sample_measurements, tmp_path, monkeypatch):
        """Saved JSON must contain run_id, timestamp, and results."""
        monkeypatch.chdir(tmp_path)
        results = {
            "greenlee": {
                "measurements": sample_measurements,
                "statistics": tester.calculate_statistics(sample_measurements),
            }
        }
        path = tester.save_results(results)
        with open(path) as f:
            data = json.load(f)
        assert "run_id" in data
        assert "timestamp" in data
        assert "results" in data
        assert "greenlee" in data["results"]


# ── sample — edge cases & errors ────────────────────────────────────

@pytest.mark.unit
class TestSampleEdgeCases:

    @patch("src.testing.ammeter_tester.client.request_current_from_ammeter")
    def test_client_returns_none_no_measurement_added(self, mock_client, tester):
        """If client returns None, measurement is skipped — list shorter than expected."""
        mock_client.return_value = None
        results = tester.sample("greenlee", 3, 10, 1.0)
        assert len(results) == 0

    @patch("src.testing.ammeter_tester.client.request_current_from_ammeter")
    def test_zero_num_measurements_raises(self, mock_client, tester):
        """num_measurements=0 must raise ValueError."""
        with pytest.raises(ValueError):
            tester.sample("greenlee", 0, 10, 0.5)

    @patch("src.testing.ammeter_tester.client.request_current_from_ammeter")
    def test_connection_refused_raises(self, mock_client, tester):
        """ConnectionRefusedError from client must propagate up."""
        mock_client.side_effect = ConnectionRefusedError
        with pytest.raises(ConnectionRefusedError):
            tester.sample("greenlee", 3, 10, 1.0)


# ── calculate_statistics — edge cases ───────────────────────────────

@pytest.mark.unit
class TestCalculateStatisticsEdgeCases:

    def test_result_has_all_required_keys(self, tester, sample_measurements):
        """Statistics dict must contain all 6 required keys."""
        result = tester.calculate_statistics(sample_measurements)
        assert set(result.keys()) == {"count", "mean", "median", "std", "min", "max"}

    def test_negative_values_statistics(self, tester, negative_measurements):
        """Statistics must work correctly on negative values."""
        result = tester.calculate_statistics(negative_measurements)
        assert result["min"] == -2.0
        assert result["max"] == 1.0
        assert result["mean"] == -0.5