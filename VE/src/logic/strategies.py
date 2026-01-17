from abc import ABC, abstractmethod
import json 
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtCore import QRectF, QSize

class SaveStrategy(ABC):
    @abstractmethod
    def save(self, filename: str, scene):
        """
        :param filename: Путь сохранения
        :param scene: Ссылка на QGraphicsScene (источник данных)
        """
        pass


class JsonSaveStrategy(SaveStrategy):
    def save(self, filename, scene):
        # 1. Подготовка структуры
        data = {
            "version": "1.0",
            "scene": {
                "width": scene.width(),
                "height": scene.height()
            },
            "shapes": []
        }

        # 2. Сбор объектов (Инвертируем порядок для правильного Z-index при загрузке)
        # scene.items() возвращает [Top, ..., Bottom] -> нам нужно [Bottom, ..., Top]
        items = scene.items()[::-1]
        
        for item in items:
            if hasattr(item, "to_dict"):
                data["shapes"].append(item.to_dict())

        # 3. Запись (можно использовать FileManager из Части 1 или писать напрямую)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

class ImageSaveStrategy(SaveStrategy):
    def __init__(self, format_name="PNG", background_color="white"):
        self.format_name = format_name # PNG, JPG
        self.bg_color = background_color

    def save(self, filename, scene):
        # 1. Определяем размер картинки
        # sceneRect - это логический размер холста (например, 800x600)
        # itemsBoundingRect - это прямоугольник, охватывающий все нарисованное (может быть больше или меньше)
        
        # Для предсказуемости берем sceneRect (размер "листа бумаги")
        rect = scene.sceneRect()
        width = int(rect.width())
        height = int(rect.height())

        # 2. Создаем буфер изображения
        # Format_ARGB32 поддерживает прозрачность (Alpha channel)
        image = QImage(width, height, QImage.Format_ARGB32)
        
        # 3. Заливка фона
        if self.bg_color == "transparent":
            image.fill(QColor(0, 0, 0, 0)) # Полностью прозрачный
        else:
            image.fill(QColor(self.bg_color))

        # 4. Рендеринг
        painter = QPainter(image)
        # Улучшаем качество (антиалиасинг)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Рендерим сцену. 
        # target_rect (на картинке) = source_rect (со сцены)
        scene.render(painter, QRectF(image.rect()), rect)
        
        painter.end() # Важно завершить рисование перед сохранением

        # 5. Сохранение на диск
        image.save(filename, self.format_name)