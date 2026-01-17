from abc import ABC, abstractmethod
from src.logic.factory import ShapeFactory
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView
from src.logic.commands import AddShapeCommand
from src.logic.commands import MoveCommand

class Tool(ABC):
    def __init__(self, canvas_view):
        self.view = canvas_view   # Ссылка на View (чтобы менять курсор)
        self.scene = canvas_view.scene # Ссылка на Сцену (чтобы добавлять объекты)

    @abstractmethod
    def mouse_press(self, event): pass

    @abstractmethod
    def mouse_move(self, event): pass

    @abstractmethod
    def mouse_release(self, event): pass


class CreationTool(Tool):
    def __init__(self, view, shape_type, undo_stack, color="black"):
        super().__init__(view)
        self.shape_type = shape_type
        self.undo_stack = undo_stack # Сохраняем ссылку
        self.shape_type = shape_type
        self.color = color
        
        # Временное хранилище
        # ✅ ВОТ ЭТО ОБЯЗАТЕЛЬНО
        self.temp_item = None
        self.start_pos = None

    def mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = self.view.mapToScene(event.pos())
            
            # 1. Создаем фигуру сразу (точка в точку)
            try:
                self.temp_item = ShapeFactory.create_shape(
                    self.shape_type,
                    self.start_pos,
                    self.start_pos, # End point = Start point
                    self.color
                )
                self.scene.addItem(self.temp_item)
            except ValueError:
                pass

    def mouse_move(self, event):
        # 2. Если мы сейчас рисуем (есть активная фигура)
        if self.temp_item and self.start_pos:
            current_pos = self.view.mapToScene(event.pos())
            
            # 3. Вызываем метод обновления геометрии
            self.temp_item.set_geometry(self.start_pos, current_pos)

    def mouse_release(self, event):
        if not self.temp_item:
            return

        end_pos = self.view.mapToScene(event.pos())

        # удаляем временную фигуру
        self.scene.removeItem(self.temp_item)

        # создаём финальную фигуру
        final_item = ShapeFactory.create_shape(
            self.shape_type,
            self.start_pos,
            end_pos,
            self.color
        )

        # ✅ ИСПРАВЛЕНИЕ:
        # вместо scene.addItem(final_item)
        command = AddShapeCommand(self.scene, final_item)
        self.undo_stack.push(command)

        self.temp_item = None
        self.start_pos = None


class SelectionTool(Tool):
    def __init__(self, view, undo_stack):
        super().__init__(view)
        self.undo_stack = undo_stack
        
        # Хранилище для начальных позиций
        # Словарь: {item: QPointF(x, y)}
        self.item_positions = {} 

    def mouse_press(self, event):
        # 1. Сначала даем Qt обработать клик (выделить объекты)
        super(type(self.view), self.view).mousePressEvent(event)
        
        # 2. Запоминаем позиции ВСЕХ выделенных объектов
        self.item_positions.clear()
        for item in self.scene.selectedItems():
            self.item_positions[item] = item.pos()

    def mouse_move(self, event):
        # Просто визуальное перемещение (Qt делает это сам)
        super(type(self.view), self.view).mouseMoveEvent(event)

    def mouse_release(self, event):
        # 1. Даем Qt завершить перемещение
        super(type(self.view), self.view).mouseReleaseEvent(event)
        
        # 2. Проверяем, сдвинулись ли объекты
        # Если выделено много объектов, это массовое перемещение.
        # Чтобы Ctrl+Z отменил всё сразу, используем МАКРОС.
        
        moved_items = []
        for item, old_pos in self.item_positions.items():
            new_pos = item.pos()
            if new_pos != old_pos:
                moved_items.append((item, old_pos, new_pos))
        
        if moved_items:
            # Начинаем транзакцию (Макрос)
            self.undo_stack.beginMacro("Move Items")
            
            for item, old_pos, new_pos in moved_items:
                cmd = MoveCommand(item, old_pos, new_pos)
                self.undo_stack.push(cmd)
                
            self.undo_stack.endMacro()
            
        # Очищаем память
        self.item_positions.clear()