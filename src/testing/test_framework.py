# test_framework.py
# Orchestrator for running ammeter tests.
# Loads test parameters from config.yaml and delegates to AmmeterTester.

from typing import Dict
from src.utils.config import load_config
from src.testing.ammeter_tester import AmmeterTester


class AmmeterTestFramework:
    def __init__(self, config_path: str = "config/config.yaml"):
        # Load test configuration and initialize the unified tester
        self.config = load_config(config_path)
        self.tester = AmmeterTester()

    def run_test(self, ammeter_type: str) -> Dict:
        """
        Run a full test cycle for the specified ammeter type.
        Reads sampling parameters from config, collects measurements,
        calculates statistics, and returns the combined result.
        ammeter_type: "greenlee" / "entes" / "circutor"
        Returns a dict with "measurements" and "statistics".
        """
        sampling = self.config["testing"]["sampling"]
        num_measurements = sampling["measurements_count"]
        duration = sampling["total_duration_seconds"]
        frequency = sampling["sampling_frequency_hz"]

        measurements = self.tester.sample(ammeter_type, num_measurements, duration, frequency)
        statistics = self.tester.calculate_statistics(measurements)

        return {
            "measurements": measurements,
            "statistics": statistics,
        }