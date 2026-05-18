from dataclasses import dataclass

@dataclass
class Task:
    """
    Модель задачи в учебном плане (узел графа).
    Хранит уникальный идентификатор, название и оценочное время выполнения.
    """
    task_id: str
    name: str
    duration_hours: float
