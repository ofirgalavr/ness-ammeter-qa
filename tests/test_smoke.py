# tests/test_smoke.py
# Smoke tests — quick sanity check that the system starts and responds.
# Runs before all other tests to verify basic connectivity.
# Emulators are started once via conftest.py session fixture.

import pytest

from Ammeters.client import request_current_from_ammeter
from src.testing.test_framework import AmmeterTestFramework


@pytest.mark.smoke
class TestSmoke:

    def test_framework_loads(self):
        """AmmeterTestFramework must initialize without errors."""
        framework = AmmeterTestFramework()
        assert framework is not None
        assert framework.config is not None

    def test_greenlee_emulator_responds(self, live_framework):
        """Greenlee emulator must respond to a single measurement request."""
        result = request_current_from_ammeter(5000, b'MEASURE_GREENLEE -get_measurement')
        assert result is not None
        assert isinstance(result[0], float)