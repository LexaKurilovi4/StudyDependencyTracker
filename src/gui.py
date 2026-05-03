from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox, QGroupBox, QFormLayout)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import networkx as nx
from src.graph_manager import GraphManager


class GraphCanvas(FigureCanvas):
    """Виджет холста Matplotlib для отрисовки графа внутри PyQt6."""

    def __init__(self, parent=None, width=5, height=5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor('#1a1b1f') 
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#1a1b1f')
        super().__init__(self.fig)

    def draw_graph(self, manager: GraphManager):
        """Отрисовка графа NetworkX."""
        self.ax.clear()
        G = manager.graph

        if len(G.nodes) == 0:
            self.ax.set_title("Добавьте задачи, чтобы увидеть граф", color='#e4e6eb', fontsize=14)
            self.ax.axis('off')
            self.draw()
            return

        pos = nx.spring_layout(G, seed=42, k=1.5)
        critical_path = manager.get_critical_path()

        node_colors = []
        labels = {}
        for node in G.nodes:
            if node in critical_path:
                node_colors.append('#ff4d4d')
            else:
                node_colors.append('#4d4f58')

            name = G.nodes[node]['name']
            dur = G.nodes[node]['duration']
            labels[node] = f"[{node}]\n{name}\n({dur} ч.)"

        nx.draw_networkx_nodes(G, pos, ax=self.ax, node_color=node_colors,
                               node_size=3500, edgecolors='white', linewidths=2)
        nx.draw_networkx_edges(G, pos, ax=self.ax, edge_color='#a0a3af',
                               arrows=True, arrowsize=20, width=2, connectionstyle="arc3,rad=0.1")
        nx.draw_networkx_labels(G, pos, labels, ax=self.ax, font_size=10, font_color='white', font_weight='bold')

        self.ax.axis('off')
        self.fig.tight_layout()
        self.draw()


class App(QMainWindow):
    """Главное окно приложения на PyQt6."""

    def __init__(self) -> None:
        super().__init__()
        self.manager = GraphManager()

        self.setWindowTitle("Менеджер учебных дедлайнов")
        self.resize(1100, 700)

        self.setStyleSheet("""
            QMainWindow { background-color: #1a1b1f; color: #e4e6eb; }
            QWidget { background-color: #1a1b1f; color: #e4e6eb; font-size: 14px; }
            QGroupBox { border: 1px solid #4d4f58; border-radius: 5px; margin-top: 15px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }
            QLineEdit { background-color: #25262c; border: 1px solid #4d4f58; padding: 5px; color: white; }
            QPushButton { background-color: #33363f; border: 1px solid #4d4f58; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #404450; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_panel = QVBoxLayout()

        task_group = QGroupBox("1. Добавить задачу")
        task_layout = QFormLayout()
        self.entry_name = QLineEdit()
        self.entry_duration = QLineEdit()
        task_layout.addRow("Название:", self.entry_name)
        task_layout.addRow("Часы (напр. 2.5):", self.entry_duration)
        self.btn_add = QPushButton("Создать")
        self.btn_add.clicked.connect(self._add_task)
        task_layout.addWidget(self.btn_add)
        task_group.setLayout(task_layout)
        left_panel.addWidget(task_group)

        dep_group = QGroupBox("2. Связать задачи (по ID из кружков)")
        dep_layout = QFormLayout()
        self.entry_from = QLineEdit()
        self.entry_to = QLineEdit()
        dep_layout.addRow("ID условия (От):", self.entry_from)
        dep_layout.addRow("ID цели (К):", self.entry_to)
        self.btn_link = QPushButton("Связать")
        self.btn_link.clicked.connect(self._add_dependency)
        dep_layout.addWidget(self.btn_link)
        dep_group.setLayout(dep_layout)
        left_panel.addWidget(dep_group)

        self.btn_clear = QPushButton("Сбросить всё")
        self.btn_clear.clicked.connect(self._clear)
        left_panel.addStretch()
        left_panel.addWidget(self.btn_clear)

        main_layout.addLayout(left_panel, 1)

        self.canvas = GraphCanvas(self, width=6, height=6, dpi=100)
        main_layout.addWidget(self.canvas, 3)

        self.canvas.draw_graph(self.manager)

    def _add_task(self):
        name = self.entry_name.text().strip()
        dur = self.entry_duration.text().strip()
        if not name or not dur:
            QMessageBox.warning(self, "Ошибка", "Введите название и часы.")
            return
        try:
            self.manager.add_task(name, float(dur))
            self.entry_name.clear()
            self.entry_duration.clear()
            self.canvas.draw_graph(self.manager)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Часы должны быть числом.")

    def _add_dependency(self):
        from_id = self.entry_from.text().strip()
        to_id = self.entry_to.text().strip()
        if not from_id or not to_id:
            return
        try:
            self.manager.add_dependency(from_id, to_id)
            self.entry_from.clear()
            self.entry_to.clear()
            self.canvas.draw_graph(self.manager)
        except (ValueError, KeyError) as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def _clear(self):
        self.manager.clear_all()
        self.canvas.draw_graph(self.manager)
