import networkx as nx
import json
from typing import List, Dict, Tuple
from src.models import Task


class GraphManager:
    """
    Менеджер для управления графом зависимостей учебных задач.
    Направление зависимостей: от базовой задачи (from_id) к зависимой (to_id).
    Это означает, что задача to_id не может быть начата до завершения from_id.
    """

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
        """
        Загружает граф из JSON файла.
        Включает валидацию формата и обработку поврежденных данных.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("Ошибка: Файл поврежден или не является валидным JSON.")
        except FileNotFoundError:
            raise ValueError("Ошибка: Файл не найден.")

        if not isinstance(data, dict):
            raise ValueError("Ошибка: Неверный формат данных (ожидается словарь).")

        if "tasks" not in data or "edges" not in data:
            raise ValueError("Ошибка: В файле отсутствуют обязательные ключи 'tasks' или 'edges'.")

        self.clear_all()
        self._id_counter = data.get("id_counter", 1)

        try:
            for t_data in data["tasks"]:
                task = Task(t_data["task_id"], t_data["name"], t_data["duration_hours"])
                self.tasks[task.task_id] = task
                self.graph.add_node(task.task_id, name=task.name, duration=task.duration_hours)

            for u, v in data["edges"]:
                self.graph.add_edge(u, v)

            if "positions" in data:
                self.positions = {node: tuple(pos) for node, pos in data["positions"].items()}
        except KeyError as e:
            self.clear_all()
            raise ValueError(f"Ошибка: Отсутствует необходимое поле в данных графа: {e}")
        except Exception as e:
            self.clear_all()
            raise ValueError(f"Критическая ошибка при загрузке: {str(e)}")
