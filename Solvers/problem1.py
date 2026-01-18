import sys
import json
import heapq
import itertools
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple

from PySide6.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene,
                               QGraphicsItem, QGraphicsEllipseItem,
                               QGraphicsLineItem, QGraphicsTextItem,
                               QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QPushButton, QFileDialog, QMessageBox, QLabel,
                               QLineEdit, QGroupBox)
from PySide6.QtCore import Qt, QRectF, QLineF, QPointF, Signal, QObject
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QPainterPathStroker, QAction


# ==========================================
# 1. Configuration (Конфигурация)
# ==========================================
class GraphConfig:
    NODE_DIAMETER = 30  # Чуть увеличил для наглядности
    NODE_RADIUS = NODE_DIAMETER / 2
    EDGE_WIDTH = 2
    MIN_DISTANCE = 50

    COLOR_BG = QColor(40, 40, 40)
    COLOR_NODE = QColor(0, 200, 255)
    COLOR_NODE_ACTIVE = QColor(255, 0, 255)
    COLOR_EDGE = QColor(200, 200, 200)
    COLOR_TEXT = QColor(255, 255, 255)

    TABLE_BG = QColor(50, 50, 50)
    TABLE_TEXT = QColor(255, 255, 255)
    TABLE_DIAGONAL = QColor(80, 80, 80)


# ==========================================
# 2. Graph Visual Entities (Виджеты Графа)
# ==========================================
class EdgeItem(QGraphicsLineItem):
    def __init__(self, source_item, dest_item):
        super().__init__()
        self.source = source_item
        self.dest = dest_item
        self.setPen(QPen(GraphConfig.COLOR_EDGE, GraphConfig.EDGE_WIDTH))
        self.setZValue(0)
        self.update_geometry()

    def update_geometry(self):
        line = QLineF(self.source.scenePos(), self.dest.scenePos())
        self.setLine(line)

    def shape(self):
        path = super().shape()
        stroker = QPainterPathStroker()
        stroker.setWidth(10)
        return stroker.createStroke(path)


class NodeItem(QGraphicsEllipseItem):
    def __init__(self, name: str, x: float, y: float):
        rect = QRectF(-GraphConfig.NODE_RADIUS, -GraphConfig.NODE_RADIUS,
                      GraphConfig.NODE_DIAMETER, GraphConfig.NODE_DIAMETER)
        super().__init__(rect)
        self.name = name
        self.edges: List[EdgeItem] = []
        self.setBrush(QBrush(GraphConfig.COLOR_NODE))
        self.setPen(QPen(Qt.NoPen))
        self.setPos(x, y)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self._create_label(name)

    def _create_label(self, text: str):
        self.label = QGraphicsTextItem(text, self)
        self.label.setDefaultTextColor(GraphConfig.COLOR_TEXT)
        # Центрируем текст относительно круга
        font = self.label.font()
        font.setBold(True)
        font.setPointSize(10)
        self.label.setFont(font)
        
        # Примерное позиционирование метки
        dx = -10 if len(text) == 1 else -15
        self.label.setPos(dx, -35)
        self.label.setFlag(QGraphicsItem.ItemIsMovable)
        self.label.setFlag(QGraphicsItem.ItemIgnoresTransformations)

    def set_highlighted(self, is_active: bool):
        color = GraphConfig.COLOR_NODE_ACTIVE if is_active else GraphConfig.COLOR_NODE
        self.setBrush(QBrush(color))

    def add_connection(self, edge: EdgeItem):
        self.edges.append(edge)

    def remove_connection(self, edge: EdgeItem):
        if edge in self.edges:
            self.edges.remove(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            for edge in self.edges:
                edge.update_geometry()
        return super().itemChange(change, value)


# ==========================================
# 3. Graph Logic Managers
# ==========================================
class ChainBuilder:
    def __init__(self):
        self.active_node: Optional[NodeItem] = None

    def start_or_continue(self, node: NodeItem) -> Optional[NodeItem]:
        prev_node = self.active_node
        if self.active_node:
            self.active_node.set_highlighted(False)
        self.active_node = node
        self.active_node.set_highlighted(True)
        return prev_node

    def reset(self):
        if self.active_node:
            self.active_node.set_highlighted(False)
            self.active_node = None


class GraphManager(QObject):
    # Сигнал передает количество узлов, а не их имена
    node_count_changed = Signal(int)

    def __init__(self, scene: QGraphicsScene):
        super().__init__()
        self.scene = scene
        self.node_counter = 0

    def get_sorted_node_names(self) -> List[str]:
        """Возвращает отсортированный список имён всех узлов"""
        nodes = [item for item in self.scene.items() if isinstance(item, NodeItem)]
        return sorted([n.name for n in nodes])
    
    def get_adjacency_dict(self) -> Dict[str, List[str]]:
        """Возвращает структуру связей графа: { 'A': ['B', 'C'], ... }"""
        adj = {}
        nodes = [item for item in self.scene.items() if isinstance(item, NodeItem)]
        
        # Инициализируем списки
        for n in nodes:
            adj[n.name] = []
            
        visited_edges = set()
        for n in nodes:
            for edge in n.edges:
                if edge in visited_edges:
                    continue
                visited_edges.add(edge)
                u_name = edge.source.name
                v_name = edge.dest.name
                if u_name in adj: adj[u_name].append(v_name)
                if v_name in adj: adj[v_name].append(u_name)
        
        return adj

    def reset(self):
        self.node_counter = 0
        self.scene.clear()
        self.node_count_changed.emit(0)

    def generate_name(self) -> str:
        n = self.node_counter
        name = ""
        while n >= 0:
            name = chr(ord('A') + (n % 26)) + name
            n = n // 26 - 1
        self.node_counter += 1
        return name

    def create_node(self, pos: QPointF, name: str = None) -> NodeItem:
        if name is None:
            name = self.generate_name()
        else:
            # Если загружаем из файла, пытаемся обновить счетчик, чтобы не было дублей
            # Это упрощенная логика
            pass 

        node = NodeItem(name, pos.x(), pos.y())
        self.scene.addItem(node)
        self.node_count_changed.emit(self.get_node_count())
        return node

    def create_edge(self, u: NodeItem, v: NodeItem):
        if u == v:
            return
        for edge in u.edges:
            if (edge.source == u and edge.dest == v) or (edge.source == v and edge.dest == u):
                return
        edge = EdgeItem(u, v)
        self.scene.addItem(edge)
        u.add_connection(edge)
        v.add_connection(edge)

    def delete_item(self, item: QGraphicsItem):
        if isinstance(item, NodeItem):
            for edge in list(item.edges):
                self.delete_item(edge)
            self.scene.removeItem(item)
            self.node_count_changed.emit(self.get_node_count())
        elif isinstance(item, EdgeItem):
            item.source.remove_connection(item)
            item.dest.remove_connection(item)
            self.scene.removeItem(item)
        elif isinstance(item, QGraphicsTextItem):
            parent = item.parentItem()
            if isinstance(parent, NodeItem):
                self.delete_item(parent)

    def get_node_count(self) -> int:
        return sum(1 for item in self.scene.items() if isinstance(item, NodeItem))

    def is_position_valid(self, pos: QPointF) -> bool:
        for item in self.scene.items():
            if isinstance(item, NodeItem):
                distance = QLineF(pos, item.scenePos()).length()
                if distance < GraphConfig.MIN_DISTANCE:
                    return False
        return True


# ==========================================
# 4. Matrix Widget (Таблица весов)
# ==========================================
class WeightMatrixWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(0)
        self.setRowCount(0)
        self.setWindowTitle("Матрица весов")
        
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {GraphConfig.TABLE_BG.name()};
                color: {GraphConfig.TABLE_TEXT.name()};
                gridline-color: #666;
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: #333;
                color: white;
                padding: 4px;
                border: 1px solid #666;
                font-weight: bold;
            }}
            QLineEdit {{ color: white; background-color: #444; }}
        """)

        self.itemChanged.connect(self.on_item_changed)
        self.horizontalHeader().setDefaultSectionSize(40)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

    def update_size(self, node_count: int):
        """Обновляет размер таблицы. Заголовки теперь ЦИФРОВЫЕ."""
        self.setRowCount(node_count)
        self.setColumnCount(node_count)

        # ЦИФРОВЫЕ заголовки (1, 2, 3...)
        labels = [str(i + 1) for i in range(node_count)]
        self.setHorizontalHeaderLabels(labels)
        self.setVerticalHeaderLabels(labels)

        self.blockSignals(True)

        for r in range(node_count):
            for c in range(node_count):
                item = self.item(r, c)
                if not item:
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.setItem(r, c, item)

                if r == c:
                    item.setFlags(Qt.ItemIsEnabled)
                    item.setBackground(QBrush(GraphConfig.TABLE_DIAGONAL))
                else:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
                    item.setBackground(QBrush(GraphConfig.TABLE_BG))

        self.blockSignals(False)

    def on_item_changed(self, item):
        """Обеспечивает симметричность матрицы"""
        row = item.row()
        col = item.column()

        if row == col:
            return

        text = item.text()

        self.blockSignals(True)
        symmetric_item = self.item(col, row)
        if symmetric_item:
            symmetric_item.setText(text)
        self.blockSignals(False)

    def get_matrix_data(self) -> List[List[int]]:
        """Возвращает матрицу весов (int). 0 если пути нет."""
        rows = self.rowCount()
        data = [[0] * rows for _ in range(rows)]
        for r in range(rows):
            for c in range(rows):
                if r == c: continue
                item = self.item(r, c)
                if item and item.text().strip():
                    try:
                        val = int(item.text())
                        data[r][c] = val
                    except ValueError:
                        pass
        return data

    def get_data_strings(self) -> List[List[str]]:
        """Для сохранения в JSON"""
        rows = self.rowCount()
        data = []
        for r in range(rows):
            row_data = []
            for c in range(rows):
                item = self.item(r, c)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data

    def set_data_strings(self, data: List[List[str]]):
        size = len(data)
        self.update_size(size)
        self.blockSignals(True)
        for r in range(size):
            for c in range(size):
                if r < len(data) and c < len(data[r]):
                    val = data[r][c]
                    item = self.item(r, c)
                    if item:
                        item.setText(val)
        self.blockSignals(False)


# ==========================================
# 5. Graph Scene & View
# ==========================================
class GraphScene(QGraphicsScene):
    def __init__(self, manager: GraphManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.chain_builder = ChainBuilder()
        self.setBackgroundBrush(QBrush(GraphConfig.COLOR_BG))
        self.setSceneRect(0, 0, 800, 600)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.chain_builder.reset()
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        pos = event.scenePos()
        item = self.itemAt(pos, self.views()[0].transform())

        if event.button() == Qt.LeftButton:
            if event.modifiers() & Qt.ShiftModifier:
                if isinstance(item, NodeItem):
                    prev_node = self.chain_builder.start_or_continue(item)
                    if prev_node:
                        self.manager.create_edge(prev_node, item)
                    event.accept()
                    return
                else:
                    self.chain_builder.reset()
            else:
                self.chain_builder.reset()

            if item is None:
                if self.manager.is_position_valid(pos):
                    self.manager.create_node(pos)
                event.accept()
                return

            super().mousePressEvent(event)

        elif event.button() == Qt.RightButton:
            self.chain_builder.reset()
            if item:
                self.manager.delete_item(item)
                event.accept()


# ==========================================
# 6. Main Application Window
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ЕГЭ Информатика: Задание 1 (Граф + Матрица)")
        self.resize(1200, 750)

        # 1. Сцена и Менеджер
        self.scene = QGraphicsScene()
        self.graph_manager = GraphManager(self.scene)
        self.scene = GraphScene(self.graph_manager, self)
        self.graph_manager.scene = self.scene

        # 2. Виджеты
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)

        self.matrix_widget = WeightMatrixWidget()

        # 3. Связь Граф -> Таблица
        # Теперь передаем только количество вершин, названия в таблице будут цифрами
        self.graph_manager.node_count_changed.connect(self.matrix_widget.update_size)

        # 4. Лейаут
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)

        # Левая часть (Матрица + Солвер)
        left_layout = QVBoxLayout()
        left_label = QLabel("Матрица весов (Вершины 1, 2, 3...)")
        left_label.setStyleSheet("font-weight: bold; color: #aaa;")
        left_layout.addWidget(left_label)
        left_layout.addWidget(self.matrix_widget)

        # ====== СОЛВЕР ======
        solver_group = QGroupBox("🔍 Поиск решения (Сопоставление)")
        solver_group.setStyleSheet("QGroupBox { border: 1px solid #666; margin-top: 10px; padding-top: 15px; font-weight: bold;}")
        solver_layout = QVBoxLayout()

        # Пояснение
        help_label = QLabel("Программа автоматически сопоставит граф (буквы) и матрицу (цифры)\nи найдет расстояние.")
        help_label.setStyleSheet("color: #aaa; font-size: 10px; font-style: italic;")
        solver_layout.addWidget(help_label)

        # Поля ввода
        input_layout = QHBoxLayout()

        self.vertex1_input = QLineEdit()
        self.vertex1_input.setPlaceholderText("A")
        self.vertex1_input.setMaximumWidth(50)
        self.vertex1_input.setAlignment(Qt.AlignCenter)
        self.vertex1_input.setStyleSheet("font-size: 14px; font-weight: bold;")

        self.vertex2_input = QLineEdit()
        self.vertex2_input.setPlaceholderText("G")
        self.vertex2_input.setMaximumWidth(50)
        self.vertex2_input.setAlignment(Qt.AlignCenter)
        self.vertex2_input.setStyleSheet("font-size: 14px; font-weight: bold;")

        self.solve_button = QPushButton("Найти расстояние")
        self.solve_button.setStyleSheet("background-color: #2a82da; color: white; font-weight: bold; padding: 5px;")
        self.solve_button.clicked.connect(self.find_shortest_path)

        input_layout.addWidget(QLabel("От (буква):"))
        input_layout.addWidget(self.vertex1_input)
        input_layout.addWidget(QLabel("До (буква):"))
        input_layout.addWidget(self.vertex2_input)
        input_layout.addWidget(self.solve_button)
        input_layout.addStretch()

        # Результат
        self.mapping_label = QLabel("Сопоставление: —")
        self.mapping_label.setStyleSheet("font-size: 11px; color: yellow; padding: 2px;")
        self.mapping_label.setWordWrap(True)

        self.result_label = QLabel("Результат: —")
        self.result_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px; color: #00ff00;")

        self.path_label = QLabel("Путь: —")
        self.path_label.setStyleSheet("font-size: 12px; padding: 5px;")

        solver_layout.addLayout(input_layout)
        solver_layout.addWidget(self.mapping_label)
        solver_layout.addWidget(self.result_label)
        solver_layout.addWidget(self.path_label)
        solver_group.setLayout(solver_layout)

        left_layout.addWidget(solver_group)
        # ====== КОНЕЦ СОЛВЕРА ======

        # Правая часть (Граф)
        right_layout = QVBoxLayout()
        right_label = QLabel("Граф (Вершины A, B, C...)")
        right_label.setStyleSheet("font-weight: bold; color: #aaa;")
        right_sublabel = QLabel("ЛКМ - узел, Shift+ЛКМ - ребро, ПКМ - удалить")
        right_sublabel.setStyleSheet("color: #777; font-size: 10px;")
        
        right_layout.addWidget(right_label)
        right_layout.addWidget(right_sublabel)
        right_layout.addWidget(self.view)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

        self.setCentralWidget(central_widget)

        # 5. Меню
        self.create_menu()

    def find_shortest_path(self):
        """
        Основная логика решения задания 1 ЕГЭ:
        1. Найти изоморфизм между графом (Буквы) и Матрицей (Индексы).
        2. Перевести запрос пользователя (Буквы) в индексы матрицы.
        3. Запустить Дейкстру.
        """
        v1_name = self.vertex1_input.text().strip().upper()
        v2_name = self.vertex2_input.text().strip().upper()

        # 1. Сброс UI
        self.mapping_label.setText("Сопоставление: Идет поиск...")
        self.result_label.setText("Результат: —")
        self.path_label.setText("Путь: —")
        QApplication.processEvents()

        # 2. Получение данных
        # Словарь смежности графа: {'A': ['B', 'C'], 'B': ['A'], ...}
        graph_adj = self.graph_manager.get_adjacency_dict()
        node_names = sorted(graph_adj.keys())
        
        # Матрица смежности (веса): [[0, 15, 0], [15, 0, 5]...]
        matrix = self.matrix_widget.get_matrix_data()
        matrix_size = len(matrix)

        # 3. Валидация
        if not v1_name or not v2_name:
            self.result_label.setText("⚠️ Введите обе вершины!")
            self.mapping_label.setText("")
            return

        if len(node_names) != matrix_size:
            self.result_label.setText("⚠️ Ошибка размеров!")
            self.mapping_label.setText(f"В графе {len(node_names)} вершин, в матрице {matrix_size}.")
            return
        
        if len(node_names) == 0:
            self.result_label.setText("⚠️ Граф пуст!")
            self.mapping_label.setText("")
            return

        if v1_name not in node_names or v2_name not in node_names:
            self.result_label.setText("⚠️ Нет таких вершин в графе!")
            self.mapping_label.setText("")
            return

        # 4. ПОИСК ИЗОМОРФИЗМА (Сопоставление Букв и Цифр)
        # Мы перебираем все перестановки индексов [0, 1, ... N-1]
        # и пытаемся назначить их буквам ['A', 'B', ...].
        
        indices = list(range(matrix_size))
        mapping = None # Будет хранить dict {'A': 0, 'B': 2, ...}
        
        # Перебор перестановок. Для N <= 8 это быстро (8! = 40320)
        # Для ЕГЭ обычно N <= 7.
        for perm in itertools.permutations(indices):
            # Создаем гипотетическое отображение: node_names[i] -> perm[i]
            temp_map = {name: idx for name, idx in zip(node_names, perm)}
            
            is_valid = True
            
            # Проверка 1: Степени вершин (кол-во ребер) должны совпадать
            # Это быстрая отсечка
            for name, idx in temp_map.items():
                graph_degree = len(graph_adj[name])
                matrix_degree = sum(1 for x in matrix[idx] if x > 0)
                if graph_degree != matrix_degree:
                    is_valid = False
                    break
            
            if not is_valid:
                continue

            # Проверка 2: Топология (ребро в графе <=> ребро в матрице)
            for name_u in node_names:
                idx_u = temp_map[name_u]
                
                # Проверяем соседей в графе
                graph_neighbors = set(graph_adj[name_u])
                
                # Проверяем соседей в матрице (тех, у кого вес > 0)
                # Нам нужно найти имена, которые соответствуют индексам матрицы
                # Для этого нужно обратное отображение
                reverse_map = {v: k for k, v in temp_map.items()}
                
                matrix_neighbors_indices = [col for col, w in enumerate(matrix[idx_u]) if w > 0]
                matrix_neighbors_names = set(reverse_map[i] for i in matrix_neighbors_indices)
                
                if graph_neighbors != matrix_neighbors_names:
                    is_valid = False
                    break
            
            if is_valid:
                mapping = temp_map
                break
        
        if mapping is None:
            self.result_label.setText("⚠️ Несовпадение топологии!")
            self.mapping_label.setText("Невозможно сопоставить граф и матрицу. Проверьте связи.")
            return

        # 5. Отображение найденного соответствия
        mapping_str = ", ".join([f"{k}→{v+1}" for k, v in sorted(mapping.items())])
        self.mapping_label.setText(f"Найдено: {mapping_str}")

        # 6. Запуск алгоритма Дейкстры по матрице
        start_idx = mapping[v1_name]
        end_idx = mapping[v2_name]
        
        dist, prev = self.dijkstra(matrix, start_idx)
        
        result_dist = dist[end_idx]
        
        if result_dist == float('inf'):
            self.result_label.setText(f"❌ Пути нет")
            self.path_label.setText("Путь: —")
        else:
            # Восстановление пути (по индексам)
            path_indices = []
            curr = end_idx
            while curr != -1:
                path_indices.append(curr)
                curr = prev[curr]
            path_indices.reverse()
            
            # Перевод индексов обратно в буквы для отображения
            # Нам нужно найти ключ по значению
            idx_to_name = {v: k for k, v in mapping.items()}
            path_names = [idx_to_name[i] for i in path_indices]
            
            self.result_label.setText(f"✅ Расстояние: {result_dist}")
            self.path_label.setText(f"Путь: {' → '.join(path_names)}")

    def dijkstra(self, matrix, start_node):
        n = len(matrix)
        dist = [float('inf')] * n
        prev = [-1] * n
        dist[start_node] = 0
        visited = [False] * n
        
        # Используем приоритетную очередь
        pq = [(0, start_node)]

        while pq:
            d, u = heapq.heappop(pq)
            
            if d > dist[u]:
                continue
            
            for v in range(n):
                weight = matrix[u][v]
                if weight > 0: # Если есть ребро
                    if dist[u] + weight < dist[v]:
                        dist[v] = dist[u] + weight
                        prev[v] = u
                        heapq.heappush(pq, (dist[v], v))
                        
        return dist, prev

    def create_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("Файл")

        save_action = QAction("Сохранить упражнение...", self)
        save_action.triggered.connect(self.save_exercise)
        file_menu.addAction(save_action)

        load_action = QAction("Загрузить упражнение...", self)
        load_action.triggered.connect(self.load_exercise)
        file_menu.addAction(load_action)

        clear_action = QAction("Очистить всё", self)
        clear_action.triggered.connect(self.clear_all)
        file_menu.addAction(clear_action)

    def clear_all(self):
        self.graph_manager.reset()
        # Таблица очистится через сигнал node_count_changed -> 0
        self.result_label.setText("Результат: —")
        self.path_label.setText("Путь: —")
        self.mapping_label.setText("Сопоставление: —")

    def save_exercise(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "JSON Files (*.json)")
        if not file_path:
            return

        # Сохраняем узлы
        nodes_data = []
        node_id_map = {} # Object -> Index
        items = [i for i in self.scene.items() if isinstance(i, NodeItem)]
        # Сортируем по имени для порядка
        items.sort(key=lambda x: x.name)
        
        for idx, node in enumerate(items):
            node_id_map[node] = idx
            nodes_data.append({
                "id": idx,
                "name": node.name,
                "x": node.pos().x(),
                "y": node.pos().y()
            })

        # Сохраняем ребра
        edges_data = []
        visited_edges = set()
        for node in items:
            for edge in node.edges:
                if edge not in visited_edges:
                    visited_edges.add(edge)
                    u_idx = node_id_map.get(edge.source)
                    v_idx = node_id_map.get(edge.dest)
                    if u_idx is not None and v_idx is not None:
                        edges_data.append({"u": u_idx, "v": v_idx})

        # Сохраняем матрицу как строки
        matrix_data = self.matrix_widget.get_data_strings()

        data = {
            "graph": {
                "nodes": nodes_data,
                "edges": edges_data,
                "node_counter": self.graph_manager.node_counter
            },
            "matrix": matrix_data
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Успех", "Упражнение сохранено!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def load_exercise(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "JSON Files (*.json)")
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.clear_all()

            graph_data = data.get("graph", {})
            nodes_list = graph_data.get("nodes", [])
            edges_list = graph_data.get("edges", [])

            self.graph_manager.node_counter = graph_data.get("node_counter", 0)

            # Восстанавливаем узлы по ID
            id_to_node = {}
            for n_data in nodes_list:
                pos = QPointF(n_data["x"], n_data["y"])
                name = n_data["name"]
                # Создаем узел с конкретным именем
                node = self.graph_manager.create_node(pos, name)
                id_to_node[n_data["id"]] = node

            # Восстанавливаем ребра
            for e_data in edges_list:
                u = id_to_node.get(e_data["u"])
                v = id_to_node.get(e_data["v"])
                if u and v:
                    self.graph_manager.create_edge(u, v)

            matrix_data = data.get("matrix", [])
            self.matrix_widget.set_data_strings(matrix_data)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.WindowText, Qt.white)
    palette.setColor(palette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(palette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.ToolTipBase, Qt.white)
    palette.setColor(palette.ColorRole.ToolTipText, Qt.white)
    palette.setColor(palette.ColorRole.Text, Qt.white)
    palette.setColor(palette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.ButtonText, Qt.white)
    palette.setColor(palette.ColorRole.BrightText, Qt.red)
    palette.setColor(palette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(palette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(palette.ColorRole.HighlightedText, Qt.black)
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())