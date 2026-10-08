from concurrent.futures import Future, ThreadPoolExecutor
import time
from typing import Optional
from task_scheduling.logger import get_logger
from task_scheduling.models.task import Task, TaskStatus
from task_scheduling.quota.controller import QuotaController
from task_scheduling.executor.base import ActionRegistry

logger = get_logger("executor.pool")

class TaskExecutor:
    def __init__(
        self,
        registry: ActionRegistry,
        quota_controller: QuotaController,
        max_workers: int = 4,
    ) -> None:
        self.registry = registry
        self.quota_controller = quota_controller
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="TaskWorker")

    def submit(self, task: Task) -> Future:
        logger.info(
            "Submitting task '%s' (action='%s', user='%s', params=%s) to worker pool",
            task.id, task.action, task.user_id, task.params
        )
        return self._pool.submit(self._run_task, task)

    def _run_task(self, task: Task):
        start_time = time.time()
        task.status = TaskStatus.RUNNING
        logger.info("Task '%s' marked RUNNING on worker thread", task.id)

        handler = self.registry.get(task.action)
        if not handler:
            err_msg = f"No handler registered for action '{task.action}'"
            logger.error("Task '%s' failed: %s", task.id, err_msg)
            task.status = TaskStatus.FAILED
            self.quota_controller.release(task.user_id, success=False)
            raise KeyError(err_msg)

        attempt = 0
        max_attempts = task.config.max_retries + 1
        last_exception: Optional[Exception] = None

        while attempt < max_attempts:
            try:
                result = handler.execute(task)
                duration = time.time() - start_time
                task.status = TaskStatus.COMPLETED
                logger.info("Task '%s' COMPLETED successfully in %.3fs", task.id, duration)
                self.quota_controller.release(task.user_id, success=True)
                return result
            except Exception as exc:
                attempt += 1
                task.retry_count = attempt
                last_exception = exc
                logger.warning(
                    "Task '%s' attempt %d/%d failed with error: %s",
                    task.id, attempt, max_attempts, exc
                )
                if attempt < max_attempts:
                    time.sleep(task.config.retry_delay_seconds)

        duration = time.time() - start_time
        task.status = TaskStatus.FAILED
        logger.error(
            "Task '%s' FAILED permanently after %d attempts (total time: %.3fs)",
            task.id, max_attempts, duration
        )
        self.quota_controller.release(task.user_id, success=False)
        if last_exception:
            raise last_exception
        raise RuntimeError("Task execution failed")

    def shutdown(self, wait: bool = True) -> None:
        logger.info("Shutting down TaskExecutor worker pool (wait=%s)", wait)
        self._pool.shutdown(wait=wait)
