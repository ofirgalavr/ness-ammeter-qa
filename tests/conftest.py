# tests/conftest.py
# Shared pytest fixtures available to all test files in this directory.

import pytest
from src.testing.AmmeterTester import AmmeterTester


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