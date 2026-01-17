from PySide6.QtGui import QUndoCommand

class AddShapeCommand(QUndoCommand):
    def __init__(self, scene, item):
        """
        :param scene: Сцена, куда добавляем
        :param item: Сама фигура (созданная, но еще не добавленная)
        """
        super().__init__()
        self.scene = scene
        self.item = item
        
        # Текст для отображения в истории (например, в меню "Undo Add Rectangle")
        # Если у фигуры есть наш метод type_name, используем его
        name = "Shape"
        if hasattr(item, "type_name"):
            name = item.type_name
        self.setText(f"Add {name}")

    def redo(self):
        # Выполняется при первом добавлении И при Ctrl+Y (Redo)
        
        # Проверка: если предмет уже на сцене, повторно добавлять нельзя (будет краш)
        if self.item.scene() != self.scene:
            self.scene.addItem(self.item)

    def undo(self):
        # Выполняется при Ctrl+Z (Undo)
        self.scene.removeItem(self.item)
        # Фигура исчезла с экрана, но self.item хранит её в памяти!


class MoveCommand(QUndoCommand):
    def __init__(self, item, old_pos, new_pos):
        super().__init__()
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.setText(f"Move {item.type_name}")

    def undo(self):
        self.item.setPos(self.old_pos)

    def redo(self):
        self.item.setPos(self.new_pos)


class DeleteCommand(QUndoCommand):
    def __init__(self, scene, item):
        super().__init__()
        self.scene = scene
        self.item = item
        self.setText(f"Delete {item.type_name}")

    def redo(self):
        # Удаляем (действие пользователя)
        self.scene.removeItem(self.item)

    def undo(self):
        # Восстанавливаем
        self.scene.addItem(self.item)

class ChangeColorCommand(QUndoCommand):
    def __init__(self, item, new_color):
        super().__init__()
        self.item = item
        self.new_color = new_color
        
        # 1. Запоминаем старый цвет ДО изменения
        # (Предполагаем, что интерфейс Shape имеет метод/свойство для чтения цвета)
        if hasattr(item, "pen"):
            self.old_color = item.pen().color().name()
        else:
            self.old_color = "#000000" # Fallback

        self.setText(f"Change Color to {new_color}")

    def redo(self):
        # Применяем новый цвет
        if hasattr(self.item, "set_active_color"):
            self.item.set_active_color(self.new_color)

    def undo(self):
        # Возвращаем старый цвет
        if hasattr(self.item, "set_active_color"):
            self.item.set_active_color(self.old_color)

class ChangeWidthCommand(QUndoCommand):
    def __init__(self, item, new_width):
        super().__init__()
        self.item = item
        self.new_width = new_width
        
        # Запоминаем старую толщину
        if hasattr(item, "pen"):
            self.old_width = item.pen().width()
        else:
            self.old_width = 1
            
        self.setText(f"Change Width to {new_width}")

    def redo(self):
        if hasattr(self.item, "set_stroke_width"):
            self.item.set_stroke_width(self.new_width)

    def undo(self):
        if hasattr(self.item, "set_stroke_width"):
            self.item.set_stroke_width(self.old_width)