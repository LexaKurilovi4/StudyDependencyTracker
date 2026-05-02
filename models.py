from dataclasses import dataclass
from typing import Optional

@dataclass
class Task:
    """Модель задачи в учебном плане."""
    task_id: str
    name: str
    duration_hours: float
    deadline: Optional[str] = None