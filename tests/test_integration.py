# tests/test_integration.py
from datetime import datetime, timezone
import unittest
from task_scheduling.models.user import User, UserQuota
from task_scheduling.models.task import Task, TaskConfig, TaskStatus
from task_scheduling.quota.controller import QuotaController
from task_scheduling.executor.base import ActionRegistry
from task_scheduling.executor.handlers import SyncActionHandler, BackupActionHandler, DeleteActionHandler
from task_scheduling.executor.worker_pool import TaskExecutor
from task_scheduling.scheduler.engine import TaskScheduler

class TestEndToEndScheduler(unittest.TestCase):
    def test_full_scheduling_workflow(self):
        quota = QuotaController()
        # Alice has concurrency 2 and quota 3
        quota.register_user(User("alice", UserQuota(max_concurrent=2, max_total_executed=3)))
        # Bob has concurrency 2 and quota 5
        quota.register_user(User("bob", UserQuota(max_concurrent=2, max_total_executed=5)))

        registry = ActionRegistry()
        registry.register("sync", SyncActionHandler())
        registry.register("backup", BackupActionHandler())
        registry.register("delete", DeleteActionHandler())

        executor = TaskExecutor(registry, quota, max_workers=4)
        scheduler = TaskScheduler(quota, executor)

        now = datetime.now(timezone.utc)
        # Alice 2 tasks (sync, delete)
        t_alice1 = Task("alice", "sync", {"target": "/data/x"}, scheduled_at=now, config=TaskConfig(priority=5))
        t_alice2 = Task("alice", "delete", {"target": "/tmp/z"}, scheduled_at=now, config=TaskConfig(priority=3))
        # Bob 1 task (backup)
        t_bob = Task("bob", "backup", {"target": "/srv/y"}, scheduled_at=now, config=TaskConfig(priority=4))

        scheduler.schedule(t_alice1)
        scheduler.schedule(t_alice2)
        scheduler.schedule(t_bob)

        dispatched = scheduler.tick(now=now)
        self.assertEqual(len(dispatched), 3)

        # Allow worker pool to finish execution
        executor.shutdown(wait=True)

        self.assertEqual(t_alice1.status, TaskStatus.COMPLETED)
        self.assertEqual(t_alice2.status, TaskStatus.COMPLETED)
        self.assertEqual(t_bob.status, TaskStatus.COMPLETED)

if __name__ == "__main__":
    unittest.main()
