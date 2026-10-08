# tests/test_scheduler.py
from datetime import datetime, timezone
import time
import unittest
from task_scheduling.models.user import User, UserQuota
from task_scheduling.models.task import Task, TaskConfig, TaskStatus
from task_scheduling.quota.controller import QuotaController
from task_scheduling.executor.base import ActionRegistry, BaseActionHandler
from task_scheduling.executor.worker_pool import TaskExecutor
from task_scheduling.scheduler.engine import TaskScheduler

class BlockingHandler(BaseActionHandler):
    def execute(self, task):
        # Hold execution briefly so tasks remain concurrent during tick
        delay = task.params.get("delay", 0.05)
        time.sleep(delay)
        return f"Done {task.params.get('msg')}"

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.quota = QuotaController()
        # Alice can run 2 tasks concurrently
        self.quota.register_user(User("alice", UserQuota(max_concurrent=2, max_total_executed=5)))
        self.registry = ActionRegistry()
        self.registry.register("blocking", BlockingHandler())
        self.executor = TaskExecutor(self.registry, self.quota, max_workers=4)
        self.scheduler = TaskScheduler(self.quota, self.executor)

    def tearDown(self):
        self.executor.shutdown(wait=True)

    def test_single_user_multiple_simultaneous_tasks(self):
        now = datetime.now(timezone.utc)
        task1 = Task("alice", "blocking", {"msg": "first", "delay": 0.02}, scheduled_at=now, config=TaskConfig(priority=1))
        task2 = Task("alice", "blocking", {"msg": "second", "delay": 0.02}, scheduled_at=now, config=TaskConfig(priority=2))
        self.scheduler.schedule(task1)
        self.scheduler.schedule(task2)

        dispatched = self.scheduler.tick(now=now)
        # Both tasks should be dispatched because Alice allows 2 concurrent tasks
        self.assertEqual(len(dispatched), 2)
        self.assertIn(task1.id, dispatched)
        self.assertIn(task2.id, dispatched)

    def test_concurrency_limiting_marks_quota_exceeded(self):
        now = datetime.now(timezone.utc)
        # Add 3 tasks when concurrency limit is 2
        for i in range(3):
            self.scheduler.schedule(
                Task("alice", "blocking", {"msg": f"task_{i}", "delay": 0.05}, scheduled_at=now, config=TaskConfig(priority=i))
            )

        dispatched = self.scheduler.tick(now=now)
        self.assertEqual(len(dispatched), 2)
        # 1 task should be deferred as QUOTA_EXCEEDED
        all_tasks = self.scheduler.get_tasks()
        quota_exceeded = [t for t in all_tasks if t.status == TaskStatus.QUOTA_EXCEEDED]
        self.assertEqual(len(quota_exceeded), 1)

if __name__ == "__main__":
    unittest.main()
