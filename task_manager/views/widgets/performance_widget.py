from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QPen
from PyQt5.QtChart import QChart, QChartView, QLineSeries


class ResourceMeter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.max_value = 100
        self.start_angle = 90 * 16  # Default start angle at top (90 degrees), converted to 1/16th of a degree
        self.background_color = QColor(220, 220, 220)
        self.foreground_color = QColor(0, 150, 0)
        self.pen_width = 8

    def set_value(self, value):
        self.value = max(0, min(value, self.max_value))
        self.update()  # Trigger a repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)

            # Calculate dimensions
            diameter = min(self.width(), self.height()) - self.pen_width
            x = (self.width() - diameter) // 2
            y = (self.height() - diameter) // 2

            # Draw background circle
            pen = QPen(self.background_color, self.pen_width)
            painter.setPen(pen)
            painter.drawEllipse(x, y, diameter, diameter)

            # Draw foreground arc based on value
            span_angle = int(-self.value / self.max_value * 360 * 16)  # Negative for clockwise, converted to 1/16th

            pen = QPen(self.foreground_color, self.pen_width)
            painter.setPen(pen)
            painter.drawArc(x, y, diameter, diameter, self.start_angle, span_angle)

            # Draw text in the center
            painter.setPen(Qt.black)
            painter.drawText(self.rect(), Qt.AlignCenter, f"{self.value}%")
        finally:
            painter.end()


class PerformanceWidget(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Заголовок
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(title_label)

        # Основной контент (метер + информация)
        content_layout = QHBoxLayout()

        # Метр
        self.meter_layout = QVBoxLayout()
        content_layout.addLayout(self.meter_layout, 1)

        # Информация
        self.info_layout = QVBoxLayout()
        content_layout.addLayout(self.info_layout, 2)

        main_layout.addLayout(content_layout)

        # График
        self.chart_layout = QVBoxLayout()
        main_layout.addLayout(self.chart_layout)

    def add_meter(self, meter):
        self.meter_layout.addWidget(meter)
        self.meter_layout.addStretch(1)

    def add_info(self, info_widget):
        self.info_layout.addWidget(info_widget)
        self.info_layout.addStretch(1)

    def add_chart(self, chart_view):
        self.chart_layout.addWidget(chart_view)