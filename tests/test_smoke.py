# tests/test_smoke.py
# Smoke tests — quick sanity check that the system starts and responds.
# Runs before all other tests to verify basic connectivity.
# Emulators are started once via conftest.py session fixture.

import logging
import pytest

from ammeters.client import request_current_from_ammeter
from src.testing.test_framework import AmmeterTestFramework

logger = logging.getLogger(__name__)


@pytest.mark.smoke
class TestSmoke:

    def test_framework_loads(self):
        """AmmeterTestFramework must initialize without errors."""
        logger.info("[smoke] test_framework_loads — initializing AmmeterTestFramework")
        framework = AmmeterTestFramework()
        assert framework is not None
        assert framework.config is not None
        logger.info("[smoke] test_framework_loads — PASSED")

    def test_greenlee_emulator_responds(self, live_framework):
        """Greenlee emulator must respond to a single measurement request."""
        logger.info("[smoke] test_greenlee_emulator_responds — sending measurement request to port 5000")
        result = request_current_from_ammeter(5000, b'MEASURE_GREENLEE -get_measurement')
        assert result is not None
        assert isinstance(result[0], float)
        logger.info(f"[smoke] test_greenlee_emulator_responds — PASSED, got {result[0]} A")