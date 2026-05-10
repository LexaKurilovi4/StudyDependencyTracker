import networkx as nx
import json
from typing import List, Dict, Tuple
from src.models import Task


class GraphManager:
    """Менеджер управления графом задач с сохранением состояния."""

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self.tasks: Dict[str, Task] = {}
        self._id_counter: int = 1
        self.positions: Dict[str, Tuple[float, float]] = {}

    def generate_id(self) -> str:
        new_id: str = str(self._id_counter)
        self._id_counter += 1
        return new_id

    def add_task(self, name: str, duration: float) -> Task:
        if duration <= 0:
            raise ValueError("Длительность задачи должна быть больше нуля.")

        task_id: str = self.generate_id()
        task: Task = Task(task_id=task_id, name=name, duration_hours=duration)
        self.tasks[task_id] = task
        self.graph.add_node(task_id, name=name, duration=duration)
        return task

    def add_dependency(self, from_id: str, to_id: str) -> None:
        if from_id not in self.tasks or to_id not in self.tasks:
            raise KeyError(f"Задачи с ID {from_id} или {to_id} не найдены.")

        self.graph.add_edge(from_id, to_id)

        try:
            nx.find_cycle(self.graph, orientation="original")
            self.graph.remove_edge(from_id, to_id)
            raise ValueError("Ошибка: Эта связь создает неразрешимый цикл!")
        except nx.NetworkXNoCycle:
            pass

    def clear_all(self) -> None:
        self.graph.clear()
        self.tasks.clear()
        self.positions.clear()
        self._id_counter = 1

    def get_critical_path(self) -> List[str]:
        """Возвращает список ID задач, составляющих самый длинный путь (критический путь)."""
        if not self.tasks:
            return []
        try:
            return nx.dag_longest_path(self.graph, weight="duration")
        except nx.NetworkXUnfeasible:
            return []

    def save_to_json(self, filepath: str) -> None:
        data = {
            "id_counter": self._id_counter,
            "tasks": [{"task_id": t.task_id, "name": t.name, "duration_hours": t.duration_hours} for t in
                      self.tasks.values()],
            "edges": list(self.graph.edges()),
            "positions": {node: list(pos) for node, pos in self.positions.items()}
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_from_json(self, filepath: str) -> None:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.clear_all()
        self._id_counter = data.get("id_counter", 1)

        for t_data in data.get("tasks", []):
            task = Task(**t_data)
            self.tasks[task.task_id] = task
            self.graph.add_node(task.task_id, name=task.name, duration=task.duration_hours)

        for u, v in data.get("edges", []):
            self.graph.add_edge(u, v)

        if "positions" in data:
            self.positions = {node: tuple(pos) for node, pos in data["positions"].items()}
