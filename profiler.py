import time
import cProfile
import pstats
import os
from src.graph_manager import GraphManager


def run_profile(size):
    print(f"Замеры скорости: Граф на {size} узлов")
    manager = GraphManager()

    start = time.time()
    for i in range(size):
        manager.add_task(f"Task {i}", 1.0)
    print(f"add_task ({size} шт): {time.time() - start:.4f} сек")

    start = time.time()
    tasks = list(manager.tasks.keys())
    for i in range(size - 1):
        manager.add_dependency(tasks[i], tasks[i + 1])
    print(f"add_dependency ({size - 1} шт): {time.time() - start:.4f} сек")

    start = time.time()
    manager.get_critical_path()
    print(f"get_critical_path: {time.time() - start:.4f} сек")

    filepath = f"profile_{size}.json"
    start = time.time()
    manager.save_to_json(filepath)
    print(f"save_to_json: {time.time() - start:.4f} сек")

    start = time.time()
    manager.load_from_json(filepath)
    print(f"load_from_json: {time.time() - start:.4f} сек")

    if os.path.exists(filepath):
        os.remove(filepath)


def detailed_profiling():
    print("Детальный отчет cProfile (поиск пути на 2000 узлов)")
    manager = GraphManager()
    for i in range(2000):
        manager.add_task(f"Task {i}", 1.0)
    tasks = list(manager.tasks.keys())
    for i in range(1999):
        manager.add_dependency(tasks[i], tasks[i + 1])

    profiler = cProfile.Profile()
    profiler.enable()
    manager.get_critical_path()
    profiler.disable()

    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(10)


if __name__ == "__main__":
    run_profile(100)
    run_profile(2000)
    detailed_profiling()
