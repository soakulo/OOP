from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsItemGroup,
)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen
from PySide6.QtGui import QPainter
from src.logic.tools import SelectionTool, CreationTool
from PySide6.QtGui import QUndoStack
from src.logic.commands import DeleteCommand

class EditorCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(0, 0, 2000, 2000)

        self.setRenderHint(QPainter.Antialiasing)
        self.setMouseTracking(True)

        self.current_tool = "select"
        self.start_pos: QPointF | None = None
        self.temp_item: QGraphicsItem | None = None
        # 1. Создаем стек истории
        self.undo_stack = QUndoStack(self)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        # Опционально: ограничим историю 50 шагами, чтобы экономить память
        self.undo_stack.setUndoLimit(50) 
        
        # 2. Обновляем инструменты
        # Теперь инструменты должны знать про undo_stack, чтобы пушить туда команды
        self.tools = {
            "select": SelectionTool(self, self.undo_stack),
            # Передаем стек в инструменты создания
            "rect": CreationTool(self, "rect", self.undo_stack),
            "line": CreationTool(self, "line", self.undo_stack),
            "ellipse": CreationTool(self, "ellipse", self.undo_stack),
            # ...
        }
        self.setFocusPolicy(Qt.StrongFocus)

    # ------------------------------------------------------------------
    # API для MainWindow
    # ------------------------------------------------------------------

    def set_tool(self, tool):
        self.current_tool = tool

        if tool == "select":
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    # ------------------------------------------------------------------
    # ГРУППИРОВКА (СТАБИЛЬНАЯ)
    # ------------------------------------------------------------------

    def group_selection(self):
        items = self.scene.selectedItems()
        print("Selected:", items)

        if len(items) < 2:
            return

        group = self.scene.createItemGroup(items)
        group.setFlag(QGraphicsItem.ItemIsSelectable, True)
        group.setFlag(QGraphicsItem.ItemIsMovable, True)
        group.setSelected(True)

        print("Группа создана")

    def ungroup_selection(self):
        for item in self.scene.selectedItems():
            if isinstance(item, QGraphicsItemGroup):
                self.scene.destroyItemGroup(item)


    def delete_selected(self):
        selected = self.scene.selectedItems()
        if not selected:
            return

        # Используем макрос, чтобы удаление 10 объектов отменялось за 1 раз
        self.undo_stack.beginMacro("Delete Selection")
        
        for item in selected:
            cmd = DeleteCommand(self.scene, item)
            self.undo_stack.push(cmd)
            
        self.undo_stack.endMacro()
    # ------------------------------------------------------------------
    # MOUSE EVENTS
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        self.tools[self.current_tool].mouse_press(event)

    def mouseMoveEvent(self, event):
        self.tools[self.current_tool].mouse_move(event)

    def mouseReleaseEvent(self, event):
        self.tools[self.current_tool].mouse_release(event)

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _prepare_item(self, item: QGraphicsItem):
        item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        item.setFlag(QGraphicsItem.ItemIsMovable, True)

    @staticmethod
    def _rect_from_points(p1: QPointF, p2: QPointF):
        x1 = min(p1.x(), p2.x())
        y1 = min(p1.y(), p2.y())
        x2 = max(p1.x(), p2.x())
        y2 = max(p1.y(), p2.y())
        return QRectF(x1, y1, x2 - x1, y2 - y1)