# tests/test_config.py
import json
import os
import tempfile
import unittest
from task_scheduling.config import load_config_from_dict, load_config_from_file

class TestConfig(unittest.TestCase):
    def test_load_config_from_dict(self):
        data = {
            "settings": {
                "max_workers": 2,
                "log_level": "DEBUG",
            },
            "users": [
                {
                    "id": "alice",
                    "quota": {
                        "max_concurrent": 2,
                        "max_total_executed": 4,
                    },
                }
            ],
            "tasks": [
                {
                    "user_id": "alice",
                    "action": "sync",
                    "params": {"target": "/test/path"},
                    "config": {
                        "priority": 10,
                        "timeout_seconds": 20.0,
                        "max_retries": 1,
                        "retry_delay_seconds": 0.5,
                    },
                }
            ],
        }

        app_config = load_config_from_dict(data)
        self.assertEqual(app_config.max_workers, 2)
        self.assertEqual(app_config.log_level, "DEBUG")
        self.assertEqual(len(app_config.users), 1)
        self.assertEqual(app_config.users[0].id, "alice")
        self.assertEqual(app_config.users[0].quota.max_concurrent, 2)
        self.assertEqual(app_config.users[0].quota.max_total_executed, 4)

        self.assertEqual(len(app_config.tasks), 1)
        task = app_config.tasks[0]
        self.assertEqual(task.user_id, "alice")
        self.assertEqual(task.action, "sync")
        self.assertEqual(task.params["target"], "/test/path")
        self.assertEqual(task.config.priority, 10)
        self.assertEqual(task.config.timeout_seconds, 20.0)

    def test_load_config_from_file(self):
        data = {
            "users": [{"id": "bob", "quota": {"max_concurrent": 1, "max_total_executed": 2}}],
            "tasks": [{"user_id": "bob", "action": "backup", "params": {"target": "/srv/b"}}],
        }
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            app_config = load_config_from_file(temp_path)
            self.assertEqual(len(app_config.users), 1)
            self.assertEqual(app_config.users[0].id, "bob")
            self.assertEqual(len(app_config.tasks), 1)
            self.assertEqual(app_config.tasks[0].action, "backup")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
