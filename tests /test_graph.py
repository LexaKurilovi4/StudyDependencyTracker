import unittest
import os
from src.graph_manager import GraphManager


class TestGraphManager(unittest.TestCase):
    def setUp(self):
        self.manager = GraphManager()

    def test_add_task(self):
        task = self.manager.add_task("Алгебра", 3.0)
        self.assertEqual(task.name, "Алгебра")
        self.assertEqual(self.manager.tasks[task.task_id].duration_hours, 3.0)
        self.assertIn(task.task_id, self.manager.graph.nodes)

    def test_cycle_prevention(self):
        t1 = self.manager.add_task("A", 1)
        t2 = self.manager.add_task("B", 1)
        self.manager.add_dependency(t1.task_id, t2.task_id)
        with self.assertRaises(ValueError):
            self.manager.add_dependency(t2.task_id, t1.task_id)

    def test_longest_path(self):
        t1 = self.manager.add_task("Задача 1", 2)
        t2 = self.manager.add_task("Задача 2", 4)
        t3 = self.manager.add_task("Задача 3", 3)
        self.manager.add_dependency(t1.task_id, t2.task_id)
        path = self.manager.get_critical_path()
        self.assertEqual(path, [t1.task_id, t2.task_id])

    def test_json_save_load(self):
        t1 = self.manager.add_task("A", 1)
        t2 = self.manager.add_task("B", 2)
        self.manager.add_dependency(t1.task_id, t2.task_id)

        filepath = "test_dump.json"
        self.manager.save_to_json(filepath)

        new_manager = GraphManager()
        new_manager.load_from_json(filepath)

        self.assertIn(t1.task_id, new_manager.tasks)
        self.assertEqual(len(new_manager.graph.edges), 1)
        os.remove(filepath)

    def test_invalid_json(self):
        with open("bad.json", "w") as f:
            f.write("{bad_json_format")
        with self.assertRaises(ValueError):
            self.manager.load_from_json("bad.json")
        os.remove("bad.json")
