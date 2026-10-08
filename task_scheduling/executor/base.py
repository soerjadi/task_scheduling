from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from task_scheduling.logger import get_logger
from task_scheduling.models.task import Task

logger = get_logger("executor.registry")

class BaseActionHandler(ABC):
    @abstractmethod
    def execute(self, task: Task) -> Any:
        """Executes the specific action given the configured task."""
        pass

class ActionRegistry:
    def __init__(self) -> None:
        self._handlers: Dict[str, BaseActionHandler] = {}

    def register(self, action: str, handler: BaseActionHandler) -> None:
        self._handlers[action] = handler
        logger.info("Registered action handler '%s' -> %s", action, handler.__class__.__name__)

    def get(self, action: str) -> Optional[BaseActionHandler]:
        return self._handlers.get(action)
