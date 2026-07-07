import logging
import os

class TestLogger:
    def __init__(self, test_name: str):
        self._test_name = test_name
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        Set up the logger that propagates to the root logger.
        All output goes to the unified pipeline_run.log via conftest.py.
        No separate FileHandler per test — avoids cluttering results/logs/.
        """
        logger = logging.getLogger(f"test_{self._test_name}")
        logger.setLevel(logging.INFO)
        logger.propagate = True  # ← all messages go to root logger (pipeline_run.log)

        # Remove any stale handlers from previous runs
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        # No FileHandler — root logger in conftest.py handles file output
        return logger

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def warning(self, message: str):
        self.logger.warning(message)