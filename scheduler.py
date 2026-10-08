from datetime import datetime, timezone
import logging
from pathlib import Path
import sys

from task_scheduling.config import load_config_from_dict, load_config_from_file
from task_scheduling.logger import configure_logging, get_logger
from task_scheduling.quota.controller import QuotaController
from task_scheduling.executor.base import ActionRegistry
from task_scheduling.executor.handlers import (
    SyncActionHandler,
    BackupActionHandler,
    DeleteActionHandler,
)
from task_scheduling.executor.worker_pool import TaskExecutor
from task_scheduling.scheduler.engine import TaskScheduler

logger = get_logger("main")

DEFAULT_CONFIG_DICT = {
    "settings": {"max_workers": 4, "log_level": "INFO"},
    "users": [
        {"id": "alice", "quota": {"max_concurrent": 2, "max_total_executed": 3}},
        {"id": "bob", "quota": {"max_concurrent": 3, "max_total_executed": 5}},
    ],
    "tasks": [
        {
            "user_id": "alice",
            "action": "sync",
            "params": {"target": "/data/x", "bandwidth_limit_mb": 50},
            "config": {"priority": 10, "timeout_seconds": 15.0},
        },
        {
            "user_id": "bob",
            "action": "backup",
            "params": {"target": "/srv/y", "compression": "gzip"},
            "config": {"priority": 5, "timeout_seconds": 30.0},
        },
        {
            "user_id": "alice",
            "action": "delete",
            "params": {"target": "/tmp/z", "force": True},
            "config": {"priority": 8, "timeout_seconds": 10.0},
        },
    ],
}

def main(config_path: str = None):
    # 1. Resolve and Load Configuration (from file or dict)
    target_file = config_path or (sys.argv[1] if len(sys.argv) > 1 else None)
    if target_file and Path(target_file).is_file():
        app_config = load_config_from_file(target_file)
        config_source = f"file '{target_file}'"
    elif Path("config.json").is_file():
        app_config = load_config_from_file("config.json")
        config_source = "default 'config.json'"
    else:
        app_config = load_config_from_dict(DEFAULT_CONFIG_DICT)
        config_source = "embedded dictionary"

    # 2. Configure Logging
    log_level = getattr(logging, app_config.log_level.upper(), logging.INFO)
    configure_logging(log_level)
    logger.info("Loaded configuration from %s", config_source)

    # 3. Setup Quota & User Management
    quota_controller = QuotaController()
    for user in app_config.users:
        quota_controller.register_user(user)

    # 4. Setup Action Registry (Extensible Strategy Pattern)
    registry = ActionRegistry()
    registry.register("sync", SyncActionHandler())
    registry.register("backup", BackupActionHandler())
    registry.register("delete", DeleteActionHandler())

    # 5. Setup Executor and Scheduler
    executor = TaskExecutor(registry, quota_controller, max_workers=app_config.max_workers)
    scheduler = TaskScheduler(quota_controller, executor)

    # 6. Schedule Tasks
    for task in app_config.tasks:
        scheduler.schedule(task)

    # 7. Execute Scheduler Tick
    now = datetime.now(timezone.utc)
    logger.info("Triggering scheduler tick...")
    scheduler.tick(now=now)

    # Await worker pool completion for demo
    executor.shutdown(wait=True)
    logger.info("All scheduled tasks finished processing.")

if __name__ == "__main__":
    main()