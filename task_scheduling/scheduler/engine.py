from datetime import datetime, timezone
from typing import Dict, List, Optional
from task_scheduling.logger import get_logger
from task_scheduling.models.task import Task, TaskStatus
from task_scheduling.quota.controller import QuotaController
from task_scheduling.executor.worker_pool import TaskExecutor

logger = get_logger("scheduler.engine")

class TaskScheduler:
    def __init__(self, quota_controller: QuotaController, executor: TaskExecutor) -> None:
        self.quota = quota_controller
        self.executor = executor
        self._tasks: Dict[str, Task] = {}

    def schedule(self, task: Task) -> None:
        self._tasks[task.id] = task
        logger.info(
            "Scheduled task '%s' for user '%s' (action='%s', run_at='%s', priority=%d)",
            task.id, task.user_id, task.action, task.scheduled_at.isoformat(), task.config.priority
        )

    def get_tasks(self) -> List[Task]:
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def tick(self, now: Optional[datetime] = None) -> List[str]:
        current_time = now or datetime.now(timezone.utc)
        logger.info("Scheduler tick started at %s", current_time.isoformat())

        # Collect eligible tasks (PENDING or previously QUOTA_EXCEEDED)
        due_tasks: List[Task] = [
            task for task in self._tasks.values()
            if task.status in (TaskStatus.PENDING, TaskStatus.QUOTA_EXCEEDED)
            and task.scheduled_at <= current_time
        ]

        # Prioritize higher priority first
        due_tasks.sort(key=lambda t: t.config.priority, reverse=True)
        logger.info("Found %d due tasks ready for evaluation", len(due_tasks))

        dispatched_ids: List[str] = []

        for task in due_tasks:
            # Check and acquire user quota slot
            if not self.quota.acquire(task.user_id):
                task.status = TaskStatus.QUOTA_EXCEEDED
                logger.warning(
                    "Task '%s' (user '%s') deferred: quota or concurrency limit reached",
                    task.id, task.user_id
                )
                continue

            # Dispatch task asynchronously
            self.executor.submit(task)
            dispatched_ids.append(task.id)

        logger.info("Scheduler tick finished. Dispatched %d tasks", len(dispatched_ids))
        return dispatched_ids
