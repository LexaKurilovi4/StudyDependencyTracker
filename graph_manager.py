import networkx as nx
from typing import List, Dict
from models import Task

class GraphManager:
    """Менеджер управления графом задач с автогенерацией ID."""

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self.tasks: Dict[str, Task] = {}
        self._id_counter: int = 1

    def generate_id(self) -> str:
        new_id: str = str(self._id_counter)
        self._id_counter += 1
        return new_id

    def add_task(self, name: str, duration: float) -> Task:
        task_id: str = self.generate_id()
        task: Task = Task(task_id=task_id, name=name, duration_hours=duration)
        self.tasks[task_id] = task
        self.graph.add_node(task_id, name=name, duration=duration)
        return task

    def add_dependency(self, from_id: str, to_id: str) -> None:
        if from_id not in self.tasks or to_id not in self.tasks:
            raise KeyError(f"Задачи с указанными ID ({from_id} или {to_id}) не найдены.")

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
        self._id_counter = 1

    def get_critical_path(self) -> List[str]:
        if not self.tasks:
            return []
        try:
            return nx.dag_longest_path(self.graph, weight="duration")
        except nx.NetworkXUnfeasible:
            return []