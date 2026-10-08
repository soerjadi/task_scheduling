# tests/test_quota.py
import unittest
from task_scheduling.models.user import User, UserQuota
from task_scheduling.quota.controller import QuotaController

class TestQuotaController(unittest.TestCase):
    def setUp(self):
        self.controller = QuotaController()
        self.user = User(id="alice", quota=UserQuota(max_concurrent=2, max_total_executed=3))
        self.controller.register_user(self.user)

    def test_acquire_and_release_concurrency(self):
        # Acquire 1
        self.assertTrue(self.controller.acquire("alice"))
        # Acquire 2 (max concurrent reached)
        self.assertTrue(self.controller.acquire("alice"))
        # Acquire 3 should fail due to concurrency limit
        self.assertFalse(self.controller.acquire("alice"))

        # Release one task successfully
        self.controller.release("alice", success=True)
        # Should now be able to acquire again
        self.assertTrue(self.controller.acquire("alice"))

    def test_total_executed_limit(self):
        # Execute 3 tasks up to max_total_executed
        for _ in range(3):
            self.assertTrue(self.controller.acquire("alice"))
            self.controller.release("alice", success=True)

        # 4th acquire should fail due to total executed quota
        self.assertFalse(self.controller.acquire("alice"))

    def test_unregistered_user(self):
        self.assertFalse(self.controller.acquire("unknown_user"))

if __name__ == "__main__":
    unittest.main()
