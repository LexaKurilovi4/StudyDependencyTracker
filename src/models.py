from dataclasses import dataclass

@dataclass
class Task:
    """Модель задачи в учебном плане."""
    task_id: str
    name: str
    duration_hours: float
