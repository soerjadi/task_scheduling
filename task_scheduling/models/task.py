from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict
import uuid

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    QUOTA_EXCEEDED = "quota_exceeded"

@dataclass
class TaskConfig:
    priority: int = 0
    timeout_seconds: float = 30.0
    max_retries: int = 0
    retry_delay_seconds: float = 1.0

@dataclass
class Task:
    user_id: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    scheduled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    config: TaskConfig = field(default_factory=TaskConfig)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
