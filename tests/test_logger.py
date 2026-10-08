# tests/test_logger.py
import logging
import unittest
from task_scheduling.logger import get_logger, configure_logging

class TestLogger(unittest.TestCase):
    def test_get_logger_returns_configured_logger(self):
        configure_logging(logging.DEBUG)
        logger = get_logger("test_module")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "task_scheduling.test_module")
        self.assertTrue(logger.isEnabledFor(logging.DEBUG))

if __name__ == "__main__":
    unittest.main()
