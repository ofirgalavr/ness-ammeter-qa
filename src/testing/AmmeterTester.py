# AmmeterTester.py
# Unified interface for communicating with all ammeter types.
# Hides port/command details from the caller — just pass the ammeter name.

from Ammeters import client
import time
from src.utils.logger import TestLogger


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
        start_time = time.time()

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