import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QMessageBox, QGroupBox, QFormLayout, QFileDialog, QSlider)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import networkx as nx

from src.models import Task
from src.graph_manager import GraphManager


class GraphCanvas(FigureCanvas):
    def __init__(self, parent=None, width=6, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor('#11111b')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#11111b')
        super().__init__(self.fig)

        self.node_colors_palette = ['#f9e2af', '#a6e3a1', '#89b4fa', '#cba6f7', '#f38ba8']

        self.node_size = 1500
        self.edge_width = 1.5

        self.selected_node = None
        self.is_dragging = False
        self.drag_offset = (0, 0)
        self.frozen_xlim = None
        self.frozen_ylim = None

        self.mpl_connect('button_press_event', self.on_press)
        self.mpl_connect('button_release_event', self.on_release)
        self.mpl_connect('motion_notify_event', self.on_motion)

    def draw_graph(self, manager: GraphManager, is_dragging=False):
        self.manager = manager

        if is_dragging and self.frozen_xlim and self.frozen_ylim:
            self.ax.set_xlim(self.frozen_xlim)
            self.ax.set_ylim(self.frozen_ylim)

        self.ax.clear()
        G = manager.graph

        if len(G.nodes) == 0:
            self.ax.axis('off')
            self.draw()
            return

        for node in G.nodes:
            if node not in manager.positions:
                if not manager.positions:
                    manager.positions[node] = (0.0, 0.0)
                else:
                    last_node = list(manager.positions.keys())[-1]
                    last_x, last_y = manager.positions[last_node]
                    manager.positions[node] = (last_x - 1.0, last_y + 1.0)

        pos = manager.positions
        node_colors_assignment = [self.node_colors_palette[int(node) % len(self.node_colors_palette)] for node in
                                  G.nodes]
        edge_colors = ['#585b70' for edge in G.edges]

        nx.draw_networkx_nodes(G, pos, ax=self.ax, node_color=node_colors_assignment,
                               node_size=self.node_size, edgecolors='white', linewidths=1.5)

        nx.draw_networkx_edges(G, pos, ax=self.ax, edge_color=edge_colors, arrows=True,
                               arrowsize=20, width=self.edge_width)

        label_color = '#cdd6f4'
        for node, (x, y) in pos.items():
            label_text = f"[{node}]\n{G.nodes[node]['name']}\n({G.nodes[node]['duration']} ч)"
            self.ax.text(x + 0.3, y + 0.3, label_text, fontsize=9, fontweight='bold', color=label_color,
                         bbox=dict(facecolor='#1e1e2e', alpha=0.6, edgecolor='none'))

        if is_dragging and self.frozen_xlim and self.frozen_ylim:
            self.ax.set_xlim(self.frozen_xlim)
            self.ax.set_ylim(self.frozen_ylim)
        else:
            xs, ys = zip(*pos.values())
            x_range = max(xs) - min(xs)
            y_range = max(ys) - min(ys)
            x_margin = max(x_range * 0.2, 2.0)
            y_margin = max(y_range * 0.2, 2.0)
            self.ax.set_xlim(min(xs) - x_margin, max(xs) + x_margin)
            self.ax.set_ylim(min(ys) - y_margin, max(ys) + y_margin)

        self.ax.axis('off')
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        self.draw()

    def on_press(self, event):
        if event.inaxes != self.ax or not hasattr(self, 'manager'):
            return

        self.frozen_xlim = self.ax.get_xlim()
        self.frozen_ylim = self.ax.get_ylim()

        min_dist = float('inf')
        closest_node = None

        for node, (x, y) in self.manager.positions.items():
            dist = (event.xdata - x) ** 2 + (event.ydata - y) ** 2
            if dist < min_dist:
                min_dist = dist
                closest_node = node

        if closest_node is not None and min_dist < 0.5:
            self.selected_node = closest_node
            self.is_dragging = True
            nx_x, nx_y = self.manager.positions[closest_node]
            self.drag_offset = (nx_x - event.xdata, nx_y - event.ydata)
        else:
            self.selected_node = None
            self.is_dragging = False

    def on_release(self, event):
        self.selected_node = None
        self.is_dragging = False
        self.frozen_xlim = None
        self.frozen_ylim = None
        if hasattr(self, 'manager') and self.manager.graph.nodes:
            self.draw_graph(self.manager, is_dragging=False)

    def on_motion(self, event):
        if self.is_dragging and self.selected_node and event.inaxes == self.ax:
            dx, dy = self.drag_offset
            self.manager.positions[self.selected_node] = (event.xdata + dx, event.ydata + dy)
            self.draw_graph(self.manager, is_dragging=True)


class App(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.manager = GraphManager()
        self.autosave_path = "autosave.json"

        if os.path.exists(self.autosave_path):
            try:
                self.manager.load_from_json(self.autosave_path)
            except Exception:
                pass

        self.setWindowTitle("Менеджер учебных дедлайнов")
        self.resize(1150, 750)
        self.setStyleSheet(
            "QMainWindow { background-color: #1a1b1f; color: #e4e6eb; font-family: 'Arial'; font-size: 13px; }")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        task_group = QGroupBox("1. Добавить задачу")
        task_group.setStyleSheet(
            "QGroupBox { border: 1px solid #4d4f58; border-radius: 5px; margin-top: 10px; font-weight: bold; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        task_layout = QFormLayout()
        self.entry_name = QLineEdit()
        self.entry_duration = QLineEdit()
        task_layout.addRow("Название:", self.entry_name)
        task_layout.addRow("Часы:", self.entry_duration)
        self.btn_add = QPushButton("Создать")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.clicked.connect(self._add_task)
        task_layout.addWidget(self.btn_add)
        task_group.setLayout(task_layout)
        left_panel.addWidget(task_group)

        dep_group = QGroupBox("2. Связать задачи")
        dep_group.setStyleSheet(
            "QGroupBox { border: 1px solid #4d4f58; border-radius: 5px; margin-top: 10px; font-weight: bold; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        dep_layout = QFormLayout()
        self.entry_from = QLineEdit()
        self.entry_to = QLineEdit()
        dep_layout.addRow("От ID:", self.entry_from)
        dep_layout.addRow("К ID:", self.entry_to)
        self.btn_link = QPushButton("Связать")
        self.btn_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_link.clicked.connect(self._add_dependency)
        dep_layout.addWidget(self.btn_link)
        dep_group.setLayout(dep_layout)
        left_panel.addWidget(dep_group)

        settings_group = QGroupBox("3. Настройки вида")
        settings_group.setStyleSheet(
            "QGroupBox { border: 1px solid #4d4f58; border-radius: 5px; margin-top: 10px; font-weight: bold; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        settings_layout = QFormLayout()

        self.slider_node = QSlider(Qt.Orientation.Horizontal)
        self.slider_node.setRange(500, 3500)
        self.slider_node.setValue(1500)
        self.slider_node.valueChanged.connect(self._update_settings)

        self.slider_edge = QSlider(Qt.Orientation.Horizontal)
        self.slider_edge.setRange(1, 8)
        self.slider_edge.setValue(2)
        self.slider_edge.valueChanged.connect(self._update_settings)

        settings_layout.addRow("Размер узлов:", self.slider_node)
        settings_layout.addRow("Толщина линий:", self.slider_edge)
        settings_group.setLayout(settings_layout)
        left_panel.addWidget(settings_group)

        file_layout = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self._save_file)
        self.btn_load = QPushButton("Загрузить")
        self.btn_load.clicked.connect(self._load_file)
        file_layout.addWidget(self.btn_save)
        file_layout.addWidget(self.btn_load)
        left_panel.addLayout(file_layout)

        self.btn_clear = QPushButton("Сбросить всё")
        self.btn_clear.clicked.connect(self._clear)
        left_panel.addStretch()
        left_panel.addWidget(self.btn_clear)

        main_layout.addLayout(left_panel, 1)

        self.canvas = GraphCanvas(self, width=6, height=6, dpi=100)
        main_layout.addWidget(self.canvas, 3)
        self.canvas.draw_graph(self.manager)

    def _update_settings(self):
        self.canvas.node_size = self.slider_node.value()
        self.canvas.edge_width = self.slider_edge.value()
        self.canvas.draw_graph(self.manager)

    def closeEvent(self, event):
        try:
            self.manager.save_to_json(self.autosave_path)
        except Exception:
            pass
        event.accept()

    def _add_task(self):
        name = self.entry_name.text().strip()
        dur_text = self.entry_duration.text().strip()
        if not name or not dur_text:
            return
        try:
            self.manager.add_task(name, float(dur_text))
            self.entry_name.clear()
            self.entry_duration.clear()
            self.canvas.draw_graph(self.manager)
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))

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

    def _save_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить план", "", "JSON Files (*.json)")
        if path:
            self.manager.save_to_json(path)

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Загрузить план", "", "JSON Files (*.json)")
        if path:
            try:
                self.manager.load_from_json(path)
                self.canvas.draw_graph(self.manager)
            except Exception:
                pass

    def _clear(self):
        self.manager.clear_all()
        self.canvas.draw_graph(self.manager)
