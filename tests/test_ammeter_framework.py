# tests/test_ammeter_framework.py
# Unit tests for AmmeterTestFramework — config-driven orchestrator.
# Uses unittest.mock to avoid requiring live ammeter servers.

import pytest
from unittest.mock import patch, MagicMock
from src.testing.test_framework import AmmeterTestFramework


@pytest.fixture
def framework():
    """Create a fresh AmmeterTestFramework instance for each test."""
    return AmmeterTestFramework()

@pytest.mark.unit
class TestRunTest:

    def test_unknown_ammeter_raises(self, framework):
        """Unknown ammeter type must raise ValueError."""
        with pytest.raises(ValueError):
            framework.run_test("unknown")

    @patch("src.testing.AmmeterTester.client.request_current_from_ammeter")
    def test_returns_measurements_and_statistics(self, mock_client, framework):
        """run_test must return dict with measurements and statistics keys."""
        mock_client.return_value = (1.5, 1000.0)
        result = framework.run_test("greenlee")
        assert "measurements" in result
        assert "statistics" in result

    @patch("src.testing.AmmeterTester.client.request_current_from_ammeter")
    def test_measurements_length_matches_config(self, mock_client, framework):
        """Number of measurements must match config measurements_count."""
        mock_client.return_value = (1.5, 1000.0)
        result = framework.run_test("greenlee")
        expected_count = framework.config["testing"]["sampling"]["measurements_count"]
        assert len(result["measurements"]) == expected_count

    @patch("src.testing.AmmeterTester.client.request_current_from_ammeter")
    def test_statistics_keys_present(self, mock_client, framework):
        """Statistics dict must contain all required keys."""
        mock_client.return_value = (2.0, 1000.0)
        result = framework.run_test("entes")
        assert set(result["statistics"].keys()) == {"count", "mean", "median", "std", "min", "max"}