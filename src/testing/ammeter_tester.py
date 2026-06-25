# ammeter_tester.py
# Unified interface for communicating with all ammeter types.
# Hides port/command details from the caller — just pass the ammeter name.

from ammeters import client
import time
from src.utils.logger import TestLogger
import numpy as np
import uuid
import json
import os
from datetime import datetime



# Configuration: maps ammeter name -> (port, command)
AMMETER_CONFIG = {
    "greenlee": (5000, b'MEASURE_GREENLEE -get_measurement'),
    "entes":    (5001, b'MEASURE_ENTES -get_data'),
    "circutor": (5002, b'MEASURE_CIRCUTOR -get_measurement -current'),
}


class AmmeterTester:
    """
    Unified tester for all ammeter types.
    Knows which port and command belongs to each ammeter.
    """

    def measure(self, ammeter_type: str) -> None:
        """
        Send a measurement request to the specified ammeter.
        ammeter_type: "greenlee" / "entes" / "circutor"
        """
        # Look up port and command from the config dictionary
        if ammeter_type not in AMMETER_CONFIG:
            print(f"Unknown ammeter type: {ammeter_type}")
            return

        port, command = AMMETER_CONFIG[ammeter_type]
        client.request_current_from_ammeter(port, command)


    def sample(self, ammeter_type: str, num_measurements: int, duration: float, frequency: float) -> list:
        """
        Collect multiple measurements from the specified ammeter.
        ammeter_type: "greenlee" / "entes" / "circutor"
        num_measurements: how many measurements to collect
        duration: total test duration in seconds
        frequency: measurements per second (e.g. 2.0 = one every 0.5 seconds)
        Returns a list of tuples: [(value, timestamp), ...]
        """
        logger = TestLogger(f"sample_{ammeter_type}")

        # Validate ammeter type
        if ammeter_type not in AMMETER_CONFIG:
            logger.error(f"Unknown ammeter type: {ammeter_type}")
            raise ValueError(f"Unknown ammeter type: {ammeter_type}")

        # Validate parameters are positive
        if num_measurements <= 0:
            logger.error("num_measurements must be positive")
            raise ValueError("num_measurements must be positive")

        if duration <= 0:
            logger.error("duration must be positive")
            raise ValueError("duration must be positive")

        if frequency <= 0:
            logger.error("frequency must be positive")
            raise ValueError("frequency must be positive")

        # Validate parameters are consistent
        if num_measurements > duration * frequency:
            logger.error(
                f"Inconsistent parameters: {num_measurements} measurements requested "
                f"but duration={duration}s and frequency={frequency}Hz allow only "
                f"{int(duration * frequency)} measurements"
            )
            raise ValueError("Inconsistent parameters: num_measurements > duration * frequency")

        # Warn if frequency is unrealistically high (ex: >100)
        if frequency > 100:
            logger.warning(f"frequency={frequency}Hz is unrealistically high")

        # Calculate time interval between measurements
        interval = 1.0 / frequency
        measurements = []

        logger.info(f"Starting sampling: {ammeter_type}, {num_measurements} measurements, {duration}s, {frequency}Hz")

        for i in range(num_measurements):
            port, command = AMMETER_CONFIG[ammeter_type]
            try:
                result = client.request_current_from_ammeter(port, command)
                if result is None:
                    logger.error(f"No response from {ammeter_type} on measurement {i + 1}")
                else:
                    measurements.append(result)
                    logger.info(f"Measurement {i + 1}: {result[0]} A at {result[1]}")
            except ConnectionRefusedError:
                logger.error(f"Cannot connect to {ammeter_type} on port {port}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error on measurement {i + 1}: {e}")
                raise

            time.sleep(interval)

        logger.info(f"Sampling complete: {len(measurements)} measurements collected")
        return measurements
    


    def calculate_statistics(self, measurements: list) -> dict:
        """
        Calculate descriptive statistics from a list of measurements.
        measurements: list of (value, timestamp) tuples — output of sample()
        Returns a dict with mean, median, std, min, max, count.
        """
        logger = TestLogger("calculate_statistics")

        if not measurements:
            logger.error("measurements list is empty")
            raise ValueError("measurements list is empty")

        # Extract only the numeric values (index 0 in each tuple)
        values = [m[0] for m in measurements]
        arr = np.array(values)

        stats = {
            "count":  int(len(arr)),
            "mean":   round(float(np.mean(arr)), 4),
            "median": round(float(np.median(arr)), 4),
            "std":    round(float(np.std(arr, ddof=1)), 4) if len(arr) > 1 else 0.0,
            "min":    round(float(np.min(arr)), 4),
            "max":    round(float(np.max(arr)), 4),
        }

        logger.info(f"Statistics calculated: {stats}")
        return stats
    

    def compare_accuracy(self, results: dict) -> dict:
        """
        Compare measurement consistency across ammeter types using
        Coefficient of Variation (CV = std / mean * 100%).
        Lower CV = more consistent = more accurate.
        results: dict with ammeter_type as key — output of run_test()
        Returns ranking from most to least consistent, with CV and verdict per ammeter.
        """
        logger = TestLogger("compare_accuracy")

        if not results:
            logger.error("results dict is empty")
            raise ValueError("results dict is empty")

        cv_scores = {}
        for ammeter_type, data in results.items():
            stats = data["statistics"]
            mean  = stats["mean"]
            std   = stats["std"]

            if mean == 0:
                cv = float("inf")
            else:
                cv = round((std / mean) * 100, 2)

            if cv < 10:
                verdict = "excellent"
            elif cv < 30:
                verdict = "good"
            elif cv < 60:
                verdict = "moderate"
            else:
                verdict = "poor"

            cv_scores[ammeter_type] = {"cv": cv, "verdict": verdict}
            logger.info(f"{ammeter_type}: CV={cv}% ({verdict})")

        # Sort by CV ascending (lowest = most consistent)
        ranking = sorted(cv_scores.keys(), key=lambda k: cv_scores[k]["cv"])
        logger.info(f"Accuracy ranking: {ranking}")

        return {
            "ranking": ranking,
            "details": cv_scores,
        }


    def save_results(self, results: dict) -> str:
        """
        Save all ammeter test results to a single JSON file with metadata.
        results: dict with ammeter_type as key, and dict with measurements + statistics as value.
        Example: {
            "greenlee": {"measurements": [...], "statistics": {...}},
            "entes":    {"measurements": [...], "statistics": {...}},
            "circutor": {"measurements": [...], "statistics": {...}},
        }
        Returns the path to the saved file.
        """
        logger = TestLogger("save_results")

        # Validate input
        if not results:
            logger.error("results dict is empty")
            raise ValueError("results dict is empty")

        # Build result record with metadata
        run_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Convert measurements from tuples to dicts for JSON serialization
        serializable_results = {}
        for ammeter_type, data in results.items():
            serializable_results[ammeter_type] = {
                "measurements": [{"value": m[0], "timestamp": m[1]} for m in data["measurements"]],
                "statistics":   data["statistics"],
            }

        record = {
            "run_id":    run_id,
            "timestamp": timestamp,
            "results":   serializable_results,
        }

        # Save to results directory
        os.makedirs("results", exist_ok=True)
        filename = f"results/run_{timestamp}_{run_id[:8]}.json"

        try:
            with open(filename, "w") as f:
                json.dump(record, f, indent=2)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise

        return filename