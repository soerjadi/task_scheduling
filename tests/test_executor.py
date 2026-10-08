# tests/test_executor.py
import time
import unittest
from task_scheduling.models.user import User, UserQuota
from task_scheduling.models.task import Task, TaskConfig, TaskStatus
from task_scheduling.quota.controller import QuotaController
from task_scheduling.executor.base import ActionRegistry, BaseActionHandler
from task_scheduling.executor.worker_pool import TaskExecutor

class SlowAction(BaseActionHandler):
    def execute(self, task):
        time.sleep(0.05)
        return "slow_done"

class FailingAction(BaseActionHandler):
    def execute(self, task):
        raise ValueError("Simulated action failure")

class TestTaskExecutor(unittest.TestCase):
    def setUp(self):
        self.quota = QuotaController()
        self.quota.register_user(User("bob", UserQuota(max_concurrent=3, max_total_executed=10)))
        self.registry = ActionRegistry()
        self.registry.register("slow", SlowAction())
        self.registry.register("fail", FailingAction())
        self.executor = TaskExecutor(self.registry, self.quota, max_workers=2)

    def tearDown(self):
        self.executor.shutdown(wait=True)

    def test_asynchronous_execution(self):
        task = Task(user_id="bob", action="slow")
        self.quota.acquire("bob")
        future = self.executor.submit(task)
        result = future.result(timeout=1.0)
        self.assertEqual(result, "slow_done")
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        stats = self.quota.get_stats("bob")
        self.assertEqual(stats.active_count, 0)
        self.assertEqual(stats.executed_count, 1)

    def test_failure_handling(self):
        task = Task(user_id="bob", action="fail", config=TaskConfig(max_retries=1, retry_delay_seconds=0.01))
        self.quota.acquire("bob")
        future = self.executor.submit(task)
        with self.assertRaises(ValueError):
            future.result(timeout=1.0)
        self.assertEqual(task.status, TaskStatus.FAILED)

if __name__ == "__main__":
    unittest.main()
