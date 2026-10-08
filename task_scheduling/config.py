from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from task_scheduling.models.user import User, UserQuota
from task_scheduling.models.task import Task, TaskConfig

@dataclass
class AppConfig:
    users: List[User] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    max_workers: int = 4
    log_level: str = "INFO"

def parse_datetime(val: Optional[str]) -> datetime:
    if not val:
        return datetime.now(timezone.utc)
    try:
        # Handles ISO format including 'Z' suffix
        cleaned = val.replace("Z", "+00:00") if val.endswith("Z") else val
        return datetime.fromisoformat(cleaned)
    except Exception:
        return datetime.now(timezone.utc)

def load_config_from_dict(data: Dict[str, Any]) -> AppConfig:
    settings = data.get("settings", {})
    max_workers = settings.get("max_workers", 4)
    log_level = settings.get("log_level", "INFO")

    users: List[User] = []
    for u in data.get("users", []):
        q_data = u.get("quota", {})
        quota = UserQuota(
            max_concurrent=q_data.get("max_concurrent", 1),
            max_total_executed=q_data.get("max_total_executed", 10),
        )
        users.append(User(id=u["id"], quota=quota))

    tasks: List[Task] = []
    for t in data.get("tasks", []):
        cfg_data = t.get("config", {})
        config = TaskConfig(
            priority=cfg_data.get("priority", 0),
            timeout_seconds=float(cfg_data.get("timeout_seconds", 30.0)),
            max_retries=int(cfg_data.get("max_retries", 0)),
            retry_delay_seconds=float(cfg_data.get("retry_delay_seconds", 1.0)),
        )
        task = Task(
            user_id=t["user_id"],
            action=t["action"],
            params=t.get("params", {}),
            scheduled_at=parse_datetime(t.get("scheduled_at")),
            config=config,
        )
        tasks.append(task)

    return AppConfig(
        users=users,
        tasks=tasks,
        max_workers=max_workers,
        log_level=log_level,
    )

def load_config_from_file(file_path: Union[str, Path]) -> AppConfig:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return load_config_from_dict(data)
