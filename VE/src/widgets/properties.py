from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                               QSpinBox, QPushButton, QFrame, QHBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QColorDialog
from PySide6.QtWidgets import QDoubleSpinBox
from PySide6.QtGui import QColor
from src.logic.commands import ChangeColorCommand
from src.logic.commands import ChangeWidthCommand

class PropertiesPanel(QWidget):
    def __init__(self, scene, undo_stack):
        super().__init__()
        self.scene = scene # Сохраняем ссылку на сцену, чтобы читать данные
        
        self._init_ui()
        
        # --- PATTERN OBSERVER ---
        # Подписываемся на события изменения выделения в сцене
        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.spin_width.valueChanged.connect(self.on_width_changed)
        self.btn_color.clicked.connect(self.on_color_clicked)

        self.scene = scene
        self.undo_stack = undo_stack

    def _init_ui(self):
        # Ограничиваем ширину панели, чтобы она не занимала пол-экрана
        self.setFixedWidth(200)
        self.setStyleSheet("background-color: #f0f0f0; border-left: 1px solid #ccc;")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop) # Прижимаем элементы к верху
        
        # Заголовок
        title = QLabel("Свойства")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # 1. Настройка Толщины
        layout.addWidget(QLabel("Толщина обводки:"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(1, 50) # Мин 1, Макс 50 пикселей
        layout.addWidget(self.spin_width)
        
        # 2. Индикатор Цвета
        layout.addWidget(QLabel("Цвет линии:"))
        self.btn_color = QPushButton()
        self.btn_color.setFixedHeight(30)
        # Пока просто заглушка, цвет настроим кодом
        layout.addWidget(self.btn_color)
        
        # Добавляем пружину, чтобы пустое место было внизу
        layout.addStretch()

        geo_layout = QHBoxLayout()
        
        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(-10000, 10000)
        self.spin_x.setPrefix("X: ")
        self.spin_x.valueChanged.connect(self.on_geo_changed)
        
        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(-10000, 10000)
        self.spin_y.setPrefix("Y: ")
        self.spin_y.valueChanged.connect(self.on_geo_changed)
        
        geo_layout.addWidget(self.spin_x)
        geo_layout.addWidget(self.spin_y)
        layout.addLayout(geo_layout)
        # Исходное состояние: панель выключена, так как ничего не выделено
        self.setEnabled(False)
        
    def on_selection_changed(self):
        """Вызывается автоматически при клике по фигурам"""
        selected_items = self.scene.selectedItems()
        
        # Сценарий 1: Ничего не выделено (кликнули в пустоту)
        if not selected_items:
            self.setEnabled(False) # Дизаблим всю панель
            # Можно сбросить значения в дефолт
            self.spin_width.setValue(1)
            self.btn_color.setStyleSheet("background-color: transparent")
            return

        # Сценарий 2: Что-то выделено
        self.setEnabled(True) # Включаем панель
        
        # Берем первый элемент ("Lead Selection")
        item = selected_items[0]
        
        # --- ИНТРОСПЕКЦИЯ ---
        # Нам нужно достать ширину и цвет. 
        # У наших фигур (Line, Rect) есть метод pen() от QGraphicsItem.
        # У Группы (Group) его может не быть или он возвращает 0.
        
        current_width = 1
        current_color = "#000000"
        
        # Проверяем, есть ли у объекта метод pen (карандаш)
        if hasattr(item, "pen") and item.pen() is not None:
             current_width = item.pen().width()
             current_color = item.pen().color().name() # Возвращает hex string "#RRGGBB"
        
        # Особый случай для Группы (если мы не реализовали прокси-свойства в Модуле 4)
        # Мы можем договориться, что Группа возвращает дефолтные значения или значения первого ребенка.
        # Пока оставим как есть: если pen() нет, будут дефолтные значения.
        
        # --- ОБНОВЛЕНИЕ UI ---
        
        # Важнейший момент для Части 2 (предотвращение цикла),
        # но хорошая привычка писать сразу:
        self.spin_width.blockSignals(True) 
        self.spin_width.setValue(current_width)
        self.spin_width.blockSignals(False)
        
        # Красим кнопку, используя CSS
        # border: none убирает стандартную выпуклость кнопки
        self.btn_color.setStyleSheet(f"background-color: {current_color}; border: 1px solid gray;")

        item = selected_items[0]
        
        # Обновляем X и Y
        self.spin_x.blockSignals(True)
        self.spin_y.blockSignals(True)
        
        self.spin_x.setValue(item.x())
        self.spin_y.setValue(item.y())
        
        self.spin_x.blockSignals(False)
        self.spin_y.blockSignals(False)

        item = selected_items[0]
        
        # Получаем красивое имя типа
        # Вариант 1: Через наш интерфейс Shape (если реализован type_name)
        if hasattr(item, "type_name"):
            type_text = item.type_name.capitalize() # "Rect" -> "Rect"
        else:
            # Вариант 2: Через имя класса Python
            type_text = type(item).__name__
            
        # Если выделено много объектов
        if len(selected_items) > 1:
            type_text += f" (+{len(selected_items)-1})"
            
        # self.lbl_type.setText(type_text)

    def on_geo_changed(self, value):
        # Этот метод срабатывает и для X, и для Y
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            # item.setPos(x, y)
            # Берем текущие значения из спинбоксов
            new_x = self.spin_x.value()
            new_y = self.spin_y.value()
            item.setPos(new_x, new_y)
        
        self.scene.update()

    def update_width_ui(self, selected_items):
        self.spin_width.blockSignals(True)
        
        first_width = -1
        is_mixed = False
        
        # Проверяем все объекты
        for i, item in enumerate(selected_items):
            if not hasattr(item, "pen"): continue
            
            w = item.pen().width()
            
            if i == 0:
                first_width = w
            else:
                if w != first_width:
                    is_mixed = True
                    break
        
        if is_mixed:
            # Qt Hack: Ставим особое значение, которое означает "Разные"
            # SpinBox не умеет писать текст "Mixed", поэтому ставим -1 (если min=0)
            # Или просто оставляем значение первого, но красим фон спинбокса в желтый
            self.spin_width.setValue(first_width)
            self.spin_width.setStyleSheet("background-color: #fffacd;") # LightYellow
            self.spin_width.setToolTip("Выбраны объекты с разной толщиной")
        else:
            self.spin_width.setValue(first_width)
            self.spin_width.setStyleSheet("") # Сброс стиля
            self.spin_width.setToolTip("")

        self.spin_width.blockSignals(False)

    def on_width_changed(self, value):
        selected_items = self.scene.selectedItems()
        if not selected_items:
            return

        self.undo_stack.beginMacro("Change Width All")
        
        for item in selected_items:
            cmd = ChangeWidthCommand(item, value)
            self.undo_stack.push(cmd)
            
        self.undo_stack.endMacro()
        self.scene.update()

    def on_color_clicked(self):
        color = QColorDialog.getColor()
        
        if color.isValid():
            hex_color = color.name()
            # Обновляем кнопку визуально
            self.btn_color.setStyleSheet(f"background-color: {hex_color};")
            
            selected_items = self.scene.selectedItems()
            if not selected_items:
                return

            # --- НАЧАЛО ТРАНЗАКЦИИ ---
            self.undo_stack.beginMacro("Change Color All")
            
            for item in selected_items:
                # Вместо прямого изменения, создаем и пушим команду
                cmd = ChangeColorCommand(item, hex_color)
                self.undo_stack.push(cmd)
                
            # --- КОНЕЦ ТРАНЗАКЦИИ ---
            self.undo_stack.endMacro()