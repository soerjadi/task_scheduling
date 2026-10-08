from dataclasses import dataclass
import threading
from typing import Dict, Optional, Tuple
from task_scheduling.logger import get_logger
from task_scheduling.models.user import User

logger = get_logger("quota")

@dataclass
class UserStats:
    active_count: int = 0
    executed_count: int = 0

class QuotaController:
    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
        self._stats: Dict[str, UserStats] = {}
        self._lock = threading.Lock()

    def register_user(self, user: User) -> None:
        with self._lock:
            self._users[user.id] = user
            if user.id not in self._stats:
                self._stats[user.id] = UserStats()
            logger.info(
                "Registered user '%s' with quota (max_concurrent=%d, max_total=%d)",
                user.id,
                user.quota.max_concurrent,
                user.quota.max_total_executed,
            )

    def can_acquire(self, user_id: str) -> Tuple[bool, Optional[str]]:
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                return False, f"User '{user_id}' is not registered"

            stats = self._stats[user_id]
            if stats.active_count >= user.quota.max_concurrent:
                return False, f"Concurrency limit reached ({stats.active_count}/{user.quota.max_concurrent})"

            if stats.executed_count + stats.active_count >= user.quota.max_total_executed:
                return False, f"Total execution quota exceeded ({stats.executed_count + stats.active_count}/{user.quota.max_total_executed})"

            return True, None

    def acquire(self, user_id: str) -> bool:
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                logger.warning("Quota acquire denied: User '%s' is not registered", user_id)
                return False

            stats = self._stats[user_id]
            if stats.active_count >= user.quota.max_concurrent:
                logger.warning(
                    "Quota acquire denied for user '%s': concurrency limit (%d/%d)",
                    user_id, stats.active_count, user.quota.max_concurrent
                )
                return False

            if stats.executed_count + stats.active_count >= user.quota.max_total_executed:
                logger.warning(
                    "Quota acquire denied for user '%s': total quota exceeded (%d/%d)",
                    user_id, stats.executed_count + stats.active_count, user.quota.max_total_executed
                )
                return False

            stats.active_count += 1
            logger.info(
                "Quota acquired for user '%s' (active: %d, total executed: %d)",
                user_id, stats.active_count, stats.executed_count
            )
            return True

    def release(self, user_id: str, success: bool) -> None:
        with self._lock:
            stats = self._stats.get(user_id)
            if not stats:
                return

            if stats.active_count > 0:
                stats.active_count -= 1

            if success:
                stats.executed_count += 1

            logger.info(
                "Quota released for user '%s' (success=%s, active remaining: %d, total executed: %d)",
                user_id, success, stats.active_count, stats.executed_count
            )

    def get_stats(self, user_id: str) -> Optional[UserStats]:
        with self._lock:
            stats = self._stats.get(user_id)
            if stats:
                return UserStats(active_count=stats.active_count, executed_count=stats.executed_count)
            return None
