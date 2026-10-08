# tests/test_models.py
from datetime import datetime, timezone
import unittest
from task_scheduling.models.user import User, UserQuota
from task_scheduling.models.task import Task, TaskConfig, TaskStatus

class TestModels(unittest.TestCase):
    def test_user_and_quota_defaults(self):
        quota = UserQuota(max_concurrent=2, max_total_executed=5)
        user = User(id="alice", quota=quota)
        self.assertEqual(user.id, "alice")
        self.assertEqual(user.quota.max_concurrent, 2)
        self.assertEqual(user.quota.max_total_executed, 5)

    def test_task_creation_and_defaults(self):
        config = TaskConfig(priority=10, timeout_seconds=15.0, max_retries=2)
        now = datetime.now(timezone.utc)
        task = Task(
            user_id="alice",
            action="sync",
            params={"target": "/data/x"},
            scheduled_at=now,
            config=config,
        )
        self.assertTrue(bool(task.id))
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.params["target"], "/data/x")
        self.assertEqual(task.config.priority, 10)
        self.assertEqual(task.retry_count, 0)

if __name__ == "__main__":
    unittest.main()
