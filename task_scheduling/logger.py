import logging
import sys

_CONFIGURED = False

def configure_logging(level: int = logging.INFO) -> None:
    global _CONFIGURED
    root_logger = logging.getLogger("task_scheduling")
    root_logger.setLevel(level)
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] [%(threadName)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    _CONFIGURED = True

def get_logger(name: str) -> logging.Logger:
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(f"task_scheduling.{name}")
