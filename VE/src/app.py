from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QFrame,
)
from PySide6.QtGui import QAction, QKeySequence, QActionGroup
from src.widgets.properties import PropertiesPanel
from src.widgets.canvas import EditorCanvas
from PySide6.QtWidgets import QFileDialog, QMessageBox
from src.logic.strategies import JsonSaveStrategy, ImageSaveStrategy
from src.logic.factory import ShapeFactory
import json


class VectorEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Vector Editor")
        self.resize(800, 600)

        # Холст создаём СРАЗУ
        self.canvas = EditorCanvas()
        self.current_tool = "line"

        self._create_props()
        self._create_actions()
        self._create_toolbar()
        self._create_layout()
        self._connect_actions()
        self._init_undo_stack()
        self._delete_actions()

        self.statusBar().showMessage("Готов к работе")

    # ------------------------------------------------------------------
    def _init_undo_stack(self):
        # Получаем стек из канваса
        stack = self.canvas.undo_stack
        
        # --- МАГИЯ QT ---
        # QUndoStack умеет сам создавать готовые QAction!
        undo_action = stack.createUndoAction(self, "&Undo")
        undo_action.setShortcut(QKeySequence.Undo) # Ctrl+Z
        
        redo_action = stack.createRedoAction(self, "&Redo")
        redo_action.setShortcut(QKeySequence.Redo) # Ctrl+Y или Ctrl+Shift+Z
        
        # Добавляем в меню Edit
        self.edit_menu.addAction(undo_action)
        self.edit_menu.addAction(redo_action)

        undo_action = stack.createUndoAction(self, "&Undo")
        redo_action = stack.createRedoAction(self, "&Redo")
        
        # ВАЖНО: createUndoAction уже автоматически настраивает enable/disable!
        # Но если мы создавали Action вручную (как для Delete), 
        # то пришлось бы писать:
        # stack.canUndoChanged.connect(my_custom_undo_action.setEnabled)
        
        # Добавляем кнопки на тулбар для наглядности
        toolbar = self.addToolBar("Edit")
        toolbar.addAction(undo_action)
        toolbar.addAction(redo_action)

    def reset_workspace(self):
        # 1. Удаляем визуальные объекты
        self.canvas.scene.clear()
        
        # 2. Забываем историю (Кнопки Undo/Redo станут серыми)
        self.canvas.undo_stack.clear()

    def _collect_scene_data(self):
        # 1. Метаданные
        project_data = {
            "version": "1.0",
            "scene": {
                "width": self.canvas.scene.width(),
                "height": self.canvas.scene.height()
            },
            "shapes": []
        }
        
        # 2. Сбор фигур
        # scene.items() возвращает объекты от верхнего к нижнему.
        # Нам нужно наоборот (от фона к переднему плану), чтобы при загрузке
        # они наложились правильно.
        items_in_order = self.canvas.scene.items()[::-1]
        
        for item in items_in_order:
            # Проверяем, умеет ли объект сохраняться (наш ли это Shape?)
            # Игнорируем вспомогательные объекты (курсоры, сетку и т.д.)
            if hasattr(item, "to_dict"):
                project_data["shapes"].append(item.to_dict())
                
        return project_data
    
    def on_save_clicked(self):
        # Настройка фильтров диалога
        filters = "Vector Project (*.json);;PNG Image (*.png);;JPEG Image (*.jpg)"
        filename, selected_filter = QFileDialog.getSaveFileName(
            self, "Save File", "", filters
        )

        if not filename:
            return

        # ВЫБОР СТРАТЕГИИ
        # Логика простая: смотрим на расширение или выбранный фильтр
        strategy = None
        
        if filename.lower().endswith(".png"):
            strategy = ImageSaveStrategy("PNG", background_color="transparent")
        elif filename.lower().endswith(".jpg"):
            strategy = ImageSaveStrategy("JPG", background_color="white") # JPG не умеет в прозрачность
        else:
            # По умолчанию JSON
            strategy = JsonSaveStrategy()

        # ВЫПОЛНЕНИЕ
        try:
            # MainWindow не знает деталей сохранения. Он просто делегирует.
            strategy.save(filename, self.canvas.scene)
            self.statusBar().showMessage(f"Successfully saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file:\n{str(e)}")

    def on_open_clicked(self):
        # 1. Спрашиваем пользователя
        filters = "Vector Project (*.json)"
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Открыть проект", 
            "", 
            filters
        )
        
        if not filename:
            return
        
        try:
            # 2. Чтение и валидация
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "version" not in data or data["version"] != "1.0":
                raise ValueError("Неподдерживаемая версия файла")
            
            # 3. Сброс текущего состояния
            self.reset_workspace()
            
            # 4. Восстановление метаданных (размер сцены)
            if "scene" in data:
                width = data["scene"].get("width", 2000)
                height = data["scene"].get("height", 2000)
                self.canvas.scene.setSceneRect(0, 0, width, height)
            
            # 5. Восстановление фигур
            for shape_data in data.get("shapes", []):
                item = ShapeFactory.from_dict(shape_data)
                self.canvas.scene.addItem(item)
            
            self.statusBar().showMessage(f"Проект загружен: {filename}")
            
        except (json.JSONDecodeError, ValueError) as e:
            QMessageBox.critical(self, "Ошибка загрузки", f"Неверный формат файла: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {str(e)}")


    def _create_actions(self):
        """Все QAction в одном месте"""

        # --- File ---
        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)

        self.save_action = QAction("Save", self)
        self.save_action.setShortcut(QKeySequence.Save)

        self.open_action = QAction("Open", self)
        self.open_action.setShortcut(QKeySequence.Open)

        # --- Edit ---
        self.group_action = QAction("Group", self)
        self.group_action.setShortcut(QKeySequence("Ctrl+G"))

        self.ungroup_action = QAction("Ungroup", self)
        self.ungroup_action.setShortcut(QKeySequence("Ctrl+U"))

        # --- Tools ---
        self.tool_actions = QActionGroup(self)
        self.tool_actions.setExclusive(True)

        self.select_action = QAction("Select", self, checkable=True)
        self.line_action = QAction("Line", self, checkable=True)
        self.rect_action = QAction("Rect", self, checkable=True)
        self.ellipse_action = QAction("Ellipse", self, checkable=True)

        for action in (
            self.select_action,
            self.line_action,
            self.rect_action,
            self.ellipse_action,
        ):
            self.tool_actions.addAction(action)

        self.line_action.setChecked(True)

    # ------------------------------------------------------------------

    def _create_toolbar(self):
        """Меню и тулбар"""

        # --- Menu ---
        self.file_menu = self.menuBar().addMenu("&File")
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.exit_action)

        self.edit_menu = self.menuBar().addMenu("&Edit")
        self.edit_menu.addActions([self.group_action, self.ungroup_action])

        # --- Toolbar ---
        toolbar = self.addToolBar("Tools")
        toolbar.setMovable(False)

        # toolbar.addActions(
        #     [
        #         self.select_action,
        #         self.line_action,
        #         self.rect_action,
        #         self.ellipse_action,
        #     ]
        # )

    # ------------------------------------------------------------------

    def _create_layout(self):
        """Основная компоновка"""

        container = QWidget()
        self.setCentralWidget(container)

        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Левая панель ---
        tools_panel = QFrame()
        tools_panel.setFixedWidth(120)
        tools_panel.setStyleSheet("background-color: #f0f0f0;")

        tools_layout = QVBoxLayout(tools_panel)

        btn_select = QPushButton("Select")
        btn_line = QPushButton("Line")
        btn_rect = QPushButton("Rect")
        btn_ellipse = QPushButton("Ellipse")

        for btn in (btn_select, btn_line, btn_rect, btn_ellipse):
            btn.setCheckable(True)
            tools_layout.addWidget(btn)

        tools_layout.addStretch()

        # Связываем кнопки с QAction
        btn_select.clicked.connect(self.select_action.trigger)
        btn_line.clicked.connect(self.line_action.trigger)
        btn_rect.clicked.connect(self.rect_action.trigger)
        btn_ellipse.clicked.connect(self.ellipse_action.trigger)

        # --- Сборка ---
        main_layout.addWidget(tools_panel)
        main_layout.addWidget(self.canvas)
        # Добавляем в Layout
        # Предполагаем, что main_layout горизонтальный (QHBoxLayout)
        # [Инструменты] [ Холст ] [Свойства]
        main_layout.addWidget(self.props_panel)

        self.canvas.set_tool(self.current_tool)


    def _create_props(self):
        # Инициализируем панель свойств
        # Передаем ей сцену, чтобы она могла подписаться на сигналы
        self.props_panel = PropertiesPanel(self.canvas.scene, self.canvas.undo_stack)
        
    def _delete_actions(self):
        delete_action = QAction("Delete", self)
        delete_action.setShortcut("Delete")
        # Привязываем к методу канваса
        delete_action.triggered.connect(self.canvas.delete_selected)
        
        self.edit_menu.addAction(delete_action)
        # Важно: добавить action к самому окну, чтобы шорткат работал
        self.addAction(delete_action)
    # ------------------------------------------------------------------

    def _connect_actions(self):
        """Связи сигналов"""

        self.select_action.triggered.connect(lambda: self._set_tool("select"))
        self.line_action.triggered.connect(lambda: self._set_tool("line"))
        self.rect_action.triggered.connect(lambda: self._set_tool("rect"))
        self.ellipse_action.triggered.connect(lambda: self._set_tool("ellipse"))

        self.group_action.triggered.connect(self.canvas.group_selection)
        self.ungroup_action.triggered.connect(self.canvas.ungroup_selection)
        self.save_action.triggered.connect(self.on_save_clicked)
        self.open_action.triggered.connect(self.on_open_clicked)

    # ------------------------------------------------------------------

    def _set_tool(self, tool_name: str):
        self.current_tool = tool_name
        self.canvas.set_tool(tool_name)
        self.statusBar().showMessage(f"Инструмент: {tool_name}")