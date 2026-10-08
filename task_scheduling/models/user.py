from dataclasses import dataclass

@dataclass
class UserQuota:
    max_concurrent: int = 1
    max_total_executed: int = 10

@dataclass
class User:
    id: str
    quota: UserQuota
