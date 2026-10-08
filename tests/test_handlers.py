# tests/test_handlers.py
import unittest
from task_scheduling.models.task import Task
from task_scheduling.executor.base import ActionRegistry
from task_scheduling.executor.handlers import SyncActionHandler, BackupActionHandler, DeleteActionHandler

class TestActionHandlers(unittest.TestCase):
    def setUp(self):
        self.registry = ActionRegistry()
        self.registry.register("sync", SyncActionHandler())
        self.registry.register("backup", BackupActionHandler())
        self.registry.register("delete", DeleteActionHandler())

    def test_sync_action_execution(self):
        task = Task(user_id="alice", action="sync", params={"target": "/data/x"})
        handler = self.registry.get("sync")
        self.assertIsNotNone(handler)
        result = handler.execute(task)
        self.assertEqual(result, "Synced /data/x")

    def test_unregistered_action(self):
        handler = self.registry.get("non_existent")
        self.assertIsNone(handler)

if __name__ == "__main__":
    unittest.main()
