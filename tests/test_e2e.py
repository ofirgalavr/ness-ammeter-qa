# tests/test_e2e.py
# End-to-end test for the full ammeter testing pipeline.
# Verifies the complete flow: start emulators → measure → save results to JSON.
# Emulators are started once via conftest.py session fixture.

import json
import logging
import os
import pytest

from src.utils.visualizer import plot_results

logger = logging.getLogger("e2e")


# ── E2E test ──────────────────────────────────────────────────────────

@pytest.mark.e2e
class TestE2EFullPipeline:

    def test_full_pipeline_saves_valid_json(self, live_framework):
        """
        Full E2E test: run all 3 ammeters, save results, verify JSON file.
        Covers the complete flow from measurement to persisted result.
        """
        logger.info("[e2e] test_full_pipeline_saves_valid_json — START")

        results = {}
        for ammeter in ["greenlee", "entes", "circutor"]:
            logger.info(f"[e2e] running test for {ammeter}")
            results[ammeter] = live_framework.run_test(ammeter)

        path = live_framework.tester.save_results(results)
        logger.info(f"[e2e] results saved to {path}")

        assert os.path.exists(path), "Results file was not created"

        with open(path) as f:
            data = json.load(f)

        assert "run_id"    in data
        assert "timestamp" in data
        assert "results"   in data
        assert set(data["results"].keys()) == {"greenlee", "entes", "circutor"}

        plot_path = plot_results(results)
        assert os.path.exists(plot_path), "Plot file was not created"
        logger.info(f"[e2e] plot saved to {plot_path}")
        logger.info("[e2e] test_full_pipeline_saves_valid_json — PASSED")