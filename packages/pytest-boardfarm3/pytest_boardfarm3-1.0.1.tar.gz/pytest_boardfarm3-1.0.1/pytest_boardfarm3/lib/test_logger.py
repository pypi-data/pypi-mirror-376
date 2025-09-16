"""Log wrapper module."""

import logging
import os


class TestLogger:  # pylint: disable=too-few-public-methods
    """Log wrapper to log test steps from tests."""

    __test__ = False  # Fix PytestCollectionWarning

    def __init__(self) -> None:
        """Initialize log wrapper."""
        self._logger = logging.getLogger("test-logger")

    def log_step(self, message: str) -> None:
        """Log test step.

        :param message: Log message
        """
        testname = (
            (os.environ.get("PYTEST_CURRENT_TEST").split(" (setup)")[0])
            .split("::")[1]
            .replace(" ", "_")
        )
        self._logger.info("[*****LOGGING-STEP*****][%s][%s]", testname, message)
