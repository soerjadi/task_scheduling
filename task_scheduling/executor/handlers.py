from typing import Any
from task_scheduling.logger import get_logger
from task_scheduling.models.task import Task
from task_scheduling.executor.base import BaseActionHandler

logger = get_logger("executor.handlers")

class SyncActionHandler(BaseActionHandler):
    def execute(self, task: Task) -> Any:
        target = task.params.get("target", "unknown")
        logger.info("Executing SYNC on target='%s' for user='%s'", target, task.user_id)
        return f"Synced {target}"

class BackupActionHandler(BaseActionHandler):
    def execute(self, task: Task) -> Any:
        target = task.params.get("target", "unknown")
        logger.info("Executing BACKUP on target='%s' for user='%s'", target, task.user_id)
        return f"Backed up {target}"

class DeleteActionHandler(BaseActionHandler):
    def execute(self, task: Task) -> Any:
        target = task.params.get("target", "unknown")
        logger.info("Executing DELETE on target='%s' for user='%s'", target, task.user_id)
        return f"Deleted {target}"
