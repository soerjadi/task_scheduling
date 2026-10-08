from datetime import datetime, timezone
from task_scheduling.logger import configure_logging, get_logger
from task_scheduling.models.user import User, UserQuota
from task_scheduling.models.task import Task, TaskConfig
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

def main():
    configure_logging()
    logger.info("Initializing task scheduling & resource limitation system...")

    # 1. Setup Quota & User Management
    quota_controller = QuotaController()
    quota_controller.register_user(User("alice", UserQuota(max_concurrent=2, max_total_executed=3)))
    quota_controller.register_user(User("bob", UserQuota(max_concurrent=3, max_total_executed=5)))

    # 2. Setup Action Registry (Extensible Strategy Pattern)
    registry = ActionRegistry()
    registry.register("sync", SyncActionHandler())
    registry.register("backup", BackupActionHandler())
    registry.register("delete", DeleteActionHandler())

    # 3. Setup Executor and Scheduler
    executor = TaskExecutor(registry, quota_controller, max_workers=4)
    scheduler = TaskScheduler(quota_controller, executor)

    # 4. Schedule Initial Tasks with Configurable Parameters & Priorities
    now = datetime.now(timezone.utc)
    tasks = [
        Task(
            user_id="alice",
            action="sync",
            params={"target": "/data/x", "bandwidth_limit_mb": 50},
            scheduled_at=now,
            config=TaskConfig(priority=10, timeout_seconds=15.0),
        ),
        Task(
            user_id="bob",
            action="backup",
            params={"target": "/srv/y", "compression": "gzip"},
            scheduled_at=now,
            config=TaskConfig(priority=5, timeout_seconds=30.0),
        ),
        Task(
            user_id="alice",
            action="delete",
            params={"target": "/tmp/z", "force": True},
            scheduled_at=now,
            config=TaskConfig(priority=8, timeout_seconds=10.0),
        ),
    ]

    for task in tasks:
        scheduler.schedule(task)

    # 5. Execute tick
    logger.info("Triggering scheduler tick...")
    scheduler.tick(now=now)

    # Await worker pool completion for demo
    executor.shutdown(wait=True)
    logger.info("All scheduled tasks finished processing.")

if __name__ == "__main__":
    main()