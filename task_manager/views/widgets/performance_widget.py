# views/widgets/performance_widget.py

# Импортируем необходимые классы из PyQt5
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QSizePolicy, QLayout) # Добавили QLayout для проверки типа
from PyQt5.QtCore import Qt, QPointF, QMargins # Добавили QMargins
from PyQt5.QtGui import QColor, QPainter, QPen
# Импортируем классы для графиков
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis # Убедитесь, что QValueAxis импортирован здесь, т.к. он используется в CoreUsageWidget

# Импортируем наш логгер
from utils.loggerService.logger import logger


class ResourceMeter(QWidget):
    """
    Виджет для отображения загрузки ресурса в виде полукругового индикатора.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # logger.debug("Инициализация ResourceMeter.") # Может быть много логов, если много метров
        self.value = 0 # Текущее значение в процентах
        self.max_value = 100 # Максимальное значение (обычно 100%)
        # Начальный угол для рисования дуги (90 градусов = верх, в 1/16 долях градуса)
        self.start_angle = 90 * 16
        # Цвет фона индикатора
        self.background_color = QColor(220, 220, 220)
        # Цвет переднего плана индикатора (загрузки)
        self.foreground_color = QColor(0, 150, 0)
        self.pen_width = 8 # Ширина линии индикатора
        # logger.debug("ResourceMeter инициализирован.")


    def set_value(self, value):
        """Устанавливает текущее значение индикатора."""
        self.value = max(0, min(value, self.max_value))
        # logger.debug(f"ResourceMeter установлен в значение: {self.value:.1f}%")
        self.update() # Запрашиваем перерисовку виджета

    def paintEvent(self, event):
        """Обработчик события рисования."""
        # logger.debug("Рисование ResourceMeter.")
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing) # Включаем сглаживание для лучшего вида

            # Рассчитываем размеры для рисования круга/дуги
            diameter = min(self.width(), self.height()) - self.pen_width
            x = (self.width() - diameter) // 2
            y = (self.height() - diameter) // 2

            # Рисуем фоновый круг
            pen = QPen(self.background_color, self.pen_width)
            painter.setPen(pen)
            # Прямоугольник, в который вписывается эллипс (в данном случае круг)
            painter.drawEllipse(x, y, diameter, diameter)

            # Рисуем дугу переднего плана на основе значения
            # Угол в 1/16 долях градуса. Отрицательный угол для рисования по часовой стрелке.
            span_angle = int(-self.value / self.max_value * 360 * 16)

            pen = QPen(self.foreground_color, self.pen_width)
            painter.setPen(pen)
            # Рисуем дугу: x, y, ширина, высота, начальный угол, угол размаха
            painter.drawArc(x, y, diameter, diameter, self.start_angle, span_angle)

            # Рисуем текст (процент) в центре
            painter.setPen(Qt.black)
            # Рисуем текст по центру прямоугольника виджета
            painter.drawText(self.rect(), Qt.AlignCenter, f"{self.value:.1f}%") # Добавил .1f для одного знака после запятой
        except Exception as e:
            logger.error(f"Ошибка при рисовании ResourceMeter: {e}")
        finally:
            painter.end() # Завершаем процесс рисования


class CoreUsageWidget(QWidget):
    """
    Виджет для отображения загрузки одного ядра процессора: текстовое значение и мини-график.
    """
    def __init__(self, core_index, parent=None):
        super().__init__(parent)
        # logger.debug(f"Инициализация CoreUsageWidget для ядра {core_index + 1}.")
        self.core_index = core_index
        # Метка для отображения текстовой загрузки ядра
        self.usage_label = QLabel(f"ЦП{core_index + 1}: 0.0%") # Нумерация ядер с 1

        # Настройка мини-графика
        self.chart = QChart()
        self.chart.setBackgroundVisible(False) # Убираем фон
        self.chart.legend().hide() # Скрываем легенду
        # Устанавливаем нулевые отступы
        self.chart.setMargins(QMargins(0, 0, 0, 0))
        self.chart.layout().setContentsMargins(0, 0, 0, 0)

        # Ось X (время)
        axis_x = QValueAxis()
        axis_x.setRange(0, 60) # Диапазон 60 секунд
        axis_x.setTickCount(7) # Метки каждые 10 секунд (0, 10, ..., 60)
        axis_x.setLabelFormat("%.0f") # Формат меток оси X (целые числа)
        # axis_x.setTitleText("Seconds ago") # Заголовок оси X (убираем для компактности)
        self.chart.addAxis(axis_x, Qt.AlignBottom) # Добавляем ось X снизу

        # Ось Y (значения)
        axis_y = QValueAxis()
        axis_y.setRange(0, 100) # Диапазон загрузки от 0 до 100%
        # axis_y.setTitleText("Usage (%)") # Заголовок оси Y (убираем для компактности)
        self.chart.addAxis(axis_y, Qt.AlignLeft) # Добавляем ось Y слева

        # Серия данных для графика
        self.series = QLineSeries()
        self.chart.addSeries(self.series) # Добавляем серию на график
        self.series.attachAxis(axis_x) # Привязываем серию к оси X
        self.series.attachAxis(axis_y) # Привязываем серию к оси Y

        # Виджет для отображения графика
        self.chart_view = QChartView(self.chart)
        self.chart_view.setFixedHeight(80) # Задаем фиксированную высоту графика ядра
        # Растягиваем по горизонтали, предпочитая минимальный размер по вертикали
        self.chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Макет для размещения метки и графика
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.addWidget(self.usage_label)
        layout.addWidget(self.chart_view)
        # logger.debug(f"CoreUsageWidget для ядра {core_index + 1} инициализирован.")


    def update_usage(self, usage_percent):
        """Обновляет текстовое значение и график загрузки ядра."""
        # logger.debug(f"Обновление CoreUsageWidget для ядра {self.core_index + 1}: {usage_percent:.1f}%.")
        self.usage_label.setText(f"ЦП{self.core_index + 1}: {usage_percent:.1f}%")
        self.update_chart(new_value=usage_percent)

    def update_chart(self, new_value):
        """Добавляет новое значение на график и сдвигает старые точки."""
        current_time = self.series.count()
        self.series.append(current_time, new_value)

        # Если точек на графике больше 60, удаляем самую старую
        if self.series.count() > 60:
            self.series.remove(0)
            # Сдвигаем оставшиеся точки по оси X, чтобы график выглядел непрерывным
            for i in range(self.series.count()):
                point = self.series.pointsVector()[i]
                self.series.replace(i, QPointF(i, point.y()))

        # Обновляем диапазон оси X, чтобы он всегда показывал последние 60 секунд
        axis_x = self.chart.axes(Qt.Horizontal)[0]
        axis_x.setRange(max(0, self.series.count() - 60), max(60, self.series.count()))


class PerformanceWidget(QFrame):
    """
    Общий виджет для секции производительности (например, Процессор, Память, Диск, Сеть).
    Содержит заголовок, секцию информации (опционально метр + текст) и секцию графиков.
    """
    def __init__(self, title, parent=None):
        super().__init__(parent)
        logger.info(f"Инициализация PerformanceWidget: '{title}'.")
        # Устанавливаем стиль рамки
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)

        # Основной вертикальный макет виджета
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Заголовок секции
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(title_label)

        # Контейнер для основной информации (может содержать метр и текстовую информацию)
        # Используем QHBoxLayout для горизонтального размещения метра и текста рядом
        self.info_container_layout = QHBoxLayout()
        main_layout.addLayout(self.info_container_layout) # Добавляем этот макет в основной

        # Контейнер для графиков
        # Используем QVBoxLayout, чтобы графики или группы графиков располагались вертикально
        self.charts_layout = QVBoxLayout()
        main_layout.addLayout(self.charts_layout) # Добавляем этот макет в основной

        # Добавляем растягиватель, чтобы контент прижимался к верху
        main_layout.addStretch(1)
        logger.info(f"PerformanceWidget: '{title}' инициализирован.")


    def add_info_widget(self, widget: QWidget):
        """
        Добавляет виджет в секцию информации PerformanceWidget.
        Ожидается QWidget (например, QLabel, ResourceMeter или контейнер для них).
        """
        # logger.debug(f"Добавление виджета информации в PerformanceWidget '{self.windowTitle() or self.objectName()}'.")
        # Добавляем виджет в горизонтальный макет информации
        self.info_container_layout.addWidget(widget)

    def add_chart_view(self, widget_or_layout):
        """
        Добавляет виджет графика (QChartView) или макет с графиками (например, QGridLayout)
        в секцию графиков PerformanceWidget.
        """
        # logger.debug(f"Добавление графика/макета в PerformanceWidget '{self.windowTitle() or self.objectName()}'.")
        # Проверяем, является ли добавляемый элемент виджетом или макетом
        if isinstance(widget_or_layout, QWidget):
             # Если это виджет (например, QChartView), добавляем его напрямую
             self.charts_layout.addWidget(widget_or_layout)
        elif isinstance(widget_or_layout, QLayout):
             # Если это макет (например, QGridLayout), добавляем его как макет
             self.charts_layout.addLayout(widget_or_layout)
        else:
             logger.warning(f"Попытка добавить некорректный тип ({type(widget_or_layout)}) в PerformanceWidget charts_layout.")