from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPen, QColor, QPainterPath
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsItemGroup


class Shape(QGraphicsPathItem):
    """
    Базовый класс для всех фигур.
    Имитируем абстрактный класс без ABC (из-за конфликта метаклассов с Qt).
    """
    
    def __init__(self, color: str = "black", stroke_width: int = 2):
        super().__init__()
        
        self.color = color
        self.stroke_width = stroke_width
        
        self._setup_pen()
        self._setup_flags()

    def _setup_pen(self):
        pen = QPen(QColor(self.color))
        pen.setWidth(self.stroke_width)
        self.setPen(pen)

    def _setup_flags(self):
        # Разрешаем выделение и перемещение
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsMovable)
        # Разрешаем слать сигналы при изменении геометрии
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    # --- "Абстрактные" методы (выбрасывают ошибку, если не переопределены) ---

    @property
    def type_name(self) -> str:
        """Должен быть переопределён в наследниках"""
        raise NotImplementedError(
            f"Класс {self.__class__.__name__} должен реализовать свойство 'type_name'"
        )

    def to_dict(self) -> dict:
        """Должен быть переопределён в наследниках"""
        raise NotImplementedError(
            f"Класс {self.__class__.__name__} должен реализовать метод 'to_dict()'"
        )
    
    def set_geometry(self, start_point: QPointF, end_point: QPointF):
        """
        Метод для динамического обновления формы фигуры.
        Принимает две точки (старт рисования и текущее положение мыши).
        """
        pass
    
    # --- Общие методы для всех фигур ---
    
    def set_active_color(self, color: str):
        """Базовая реализация для Листьев (Line, Rect)"""
        self.color = color
        pen = self.pen()
        pen.setColor(QColor(color))
        self.setPen(pen)
    
    def get_base_dict(self) -> dict:
        """Базовые данные, общие для всех фигур"""
        return {
            "type": self.type_name,
            "color": self.color,
            "stroke_width": self.stroke_width,
            "pos": {"x": self.pos().x(), "y": self.pos().y()}
        }
    
    def set_stroke_width(self, width: int):
        pen = self.pen()
        pen.setWidth(width)
        self.setPen(pen)
    
    
    

class Rectangle(Shape):
    def __init__(self, x, y, w, h, color="black", stroke_width=2):
        # 1. Инициализация родителя (настройка ручки, флагов)
        super().__init__(color, stroke_width)
        
        # 2. Сохраняем "Бизнес-данные"
        # Они нужны нам для сохранения в файл (to_dict)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        
        # 3. Создаем визуальное представление
        self._create_geometry()


    def set_geometry(self, start_point, end_point):
        # 1. Сохраняем новые координаты (для будущего сохранения)
        self.x = min(start_point.x(), end_point.x())
        self.y = min(start_point.y(), end_point.y())
        self.w = abs(end_point.x() - start_point.x())
        self.h = abs(end_point.y() - start_point.y())
        
        # 2. Перестраиваем путь (QPainterPath)
        path = QPainterPath()
        path.addRect(self.x, self.y, self.w, self.h)
        
        # 3. Обновляем визуальное представление
        self.setPath(path)

    def _create_geometry(self):
        # Создаем векторный путь
        path = QPainterPath()
        path.addRect(self.x, self.y, self.w, self.h)
        
        # Передаем путь в движок Qt
        self.setPath(path)

    # --- Реализация Абстрактных методов ---

    @property
    def type_name(self) -> str:
        return "rect"

    def to_dict(self):
        return {
            "type": self.type_name,
            "pos": {"x": self.pos().x(), "y": self.pos().y()},
            "props": {
                "x": self.x,
                "y": self.y,
                "w": self.w,
                "h": self.h,
                "color": self.pen().color().name(),
                "stroke_width": self.pen().width()
            }
        }
    
class Line(Shape):
    def __init__(self, x1, y1, x2, y2, color="black", stroke_width=2):
        super().__init__(color, stroke_width)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        
        self._create_geometry()

    def _create_geometry(self):
        path = QPainterPath()
        # Инструкция: встань в начало
        path.moveTo(self.x1, self.y1)
        # Инструкция: проведи черту до конца
        path.lineTo(self.x2, self.y2)
        
        self.setPath(path)

    @property
    def type_name(self) -> str:
        return "line"

    def to_dict(self):
        return {
            "type": "line",
            "pos": {"x": self.pos().x(), "y": self.pos().y()},
            "props": {
                "x1": self.x1,
                "y1": self.y1,
                "x2": self.x2,
                "y2": self.y2,
                "color": self.pen().color().name(),
                "stroke_width": self.pen().width()
            }
        }
    def set_geometry(self, start_point, end_point):
        self.x1 = start_point.x()
        self.y1 = start_point.y()
        self.x2 = end_point.x()
        self.y2 = end_point.y()
        
        path = QPainterPath()
        path.moveTo(self.x1, self.y1)
        path.lineTo(self.x2, self.y2)
        
        self.setPath(path)

    
class Ellipse(Shape):
    def __init__(self, x, y, w, h, color="black", stroke_width=2):
        super().__init__(color, stroke_width)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self._create_geometry()

    def _create_geometry(self):
        path = QPainterPath()
        # Отличие только в методе: addEllipse вместо addRect
        path.addEllipse(self.x, self.y, self.w, self.h)
        self.setPath(path)

    @property
    def type_name(self) -> str:
        return "ellipse"

    def to_dict(self) -> dict:
        # Код идентичен Rectangle, можно было бы вынести в общий класс-предок
        # RectangularShape, но для обучения копипаста допустима для наглядности.
        return {
            "type": self.type_name,
            "pos": [self.x(), self.y()],
            "props": {
                "x": self.x, "y": self.y, 
                "w": self.w, "h": self.h,
                "color": self.pen().color().name(),
                "stroke_width": self.pen().width()
            }
        }
    def set_geometry(self, start_point, end_point):
        self.x = min(start_point.x(), end_point.x())
        self.y = min(start_point.y(), end_point.y())
        self.w = abs(end_point.x() - start_point.x())
        self.h = abs(end_point.y() - start_point.y())
        
        path = QPainterPath()
        path.addEllipse(self.x, self.y, self.w, self.h)
        
        self.setPath(path)


class Group(QGraphicsItemGroup, Shape):
    def __init__(self):
        # 1. Инициализируем Qt-часть
        super().__init__()
        
        # 2. Настраиваем флаги
        # Группа должна быть выделяемой и перемещаемой
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable, True)
        
        # ВАЖНО: setHandlesChildEvents(True) заставляет группу перехватывать
        # события мыши, адресованные её детям. 
        # Если кликнуть по линии внутри группы, событие получит сама группа.
        self.setHandlesChildEvents(True)

    @property
    def type_name(self) -> str:
        return "group"

    # --- РЕАЛИЗАЦИЯ ПАТТЕРНА COMPOSITE ---

    def set_geometry(self, start, end):
        # Группу нельзя создать растягиванием мыши (как квадрат),
        # поэтому метод оставляем пустым или выбрасываем ошибку.
        pass

    def set_active_color(self, color: str):
        """
        Рекурсивно меняет цвет всех детей.
        Внешний код (Canvas) просто вызывает group.set_active_color("red"),
        не зная, что внутри 50 объектов.
        """
        for child in self.childItems():
            # Проверяем, является ли ребенок "нашим" (унаследован от Shape)
            if isinstance(child, Shape):
                child.set_active_color(color)
            
            # Если внутри группы есть другая группа, этот код сработает рекурсивно!
    def set_stroke_width(self, width: int):
        for child in self.childItems():
            if isinstance(child, Shape):
                child.set_stroke_width(width)
                
    def to_dict(self):
        children_data = []
        for child in self.childItems():
            if hasattr(child, "to_dict"):
                children_data.append(child.to_dict())
        
        return {
            "type": "group",
            "pos": {"x": self.pos().x(), "y": self.pos().y()},
            "children": children_data
        }