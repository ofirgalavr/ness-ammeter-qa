import logging
import os
from datetime import datetime

class TestLogger:
    def __init__(self, test_name: str):
        self._test_name = test_name
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        Set up the logger with a custom formatter and file output.
        """
        # Create the logs directory
        log_dir = "results/logs"
        os.makedirs(log_dir, exist_ok=True)

        # Build log filename with timestamp and test name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"{log_dir}/{timestamp}_{self._test_name}.log"

        # Configure the logger
        logger = logging.getLogger(f"test_{self._test_name}")
        logger.setLevel(logging.INFO)          # Without this, INFO/DEBUG messages are swallowed
        logger.propagate = True                # Allow pytest to capture logs via root logger

        # Prevent duplicate handlers — getLogger returns the same object on every call
        if not logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

            # Write to per-test log file
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def warning(self, message: str):
        self.logger.warning(message) 