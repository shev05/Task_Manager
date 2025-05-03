import sys
import psutil

from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtCore import QTimer, Qt, QMargins, QPointF
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QTabWidget,
                             QLabel, QSizePolicy, QScrollArea)

from controllers.process_controller import ProcessController
from models.process_model import ProcessTableModel
from models.system_monitor import SystemMonitor
from views.widgets.performance_widget import PerformanceWidget, ResourceMeter
from views.widgets.process_table import ProcessTableView
from views.widgets.system_panel import SystemPanel


class TaskManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Диспетчер задач")
        self.setGeometry(100, 100, 1000, 700)

        # Инициализация моделей и контроллеров
        self.source_model = ProcessTableModel()
        self.system_monitor = SystemMonitor()
        self.process_controller = ProcessController()

        self.init_ui()
        self.init_timer()

    def init_ui(self):
        # Создаем главный виджет с вкладками
        self.tab_widget = QTabWidget()
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Создаем вкладки
        self.create_process_tab()
        self.create_performance_tab()

        # Устанавливаем центральный виджет
        self.setCentralWidget(self.tab_widget)

    def create_process_tab(self):
        """Создает вкладку с процессами"""
        process_tab = QWidget()
        layout = QVBoxLayout(process_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.system_panel = SystemPanel()
        layout.addWidget(self.system_panel)

        self.process_table = ProcessTableView()
        self.process_table.set_process_controller(self.process_controller)
        self.process_table.setModel(self.source_model)
        layout.addWidget(self.process_table, 1)

        self.tab_widget.addTab(process_tab, "Процессы")

    def create_performance_tab(self):
        """Создает вкладку с информацией о производительности"""
        # Создаем основной контейнер с прокруткой
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        scroll_layout.addWidget(content_widget)
        scroll_layout.addStretch(1)

        # Общие настройки для всех графиков
        def create_chart():
            chart = QChart()
            chart.setBackgroundVisible(False)
            chart.legend().hide()
            chart.setMargins(QMargins(0, 0, 0, 0))
            chart.layout().setContentsMargins(0, 0, 0, 0)

            # Ось X (время)
            axis_x = QValueAxis()
            axis_x.setRange(0, 60)
            axis_x.setTickCount(7)
            axis_x.setLabelFormat("%.0f")
            axis_x.setTitleText("Seconds ago")
            chart.addAxis(axis_x, Qt.AlignBottom)

            # Ось Y (значения)
            axis_y = QValueAxis()
            axis_y.setRange(0, 100)
            axis_y.setTitleText("Usage (%)")
            chart.addAxis(axis_y, Qt.AlignLeft)

            return chart

        # CPU Section
        cpu_section = PerformanceWidget("Процессор")
        self.cpu_meter = ResourceMeter()
        self.cpu_info_label = QLabel()
        cpu_section.add_meter(self.cpu_meter)
        cpu_section.add_info(self.cpu_info_label)

        self.cpu_chart = create_chart()
        self.cpu_series = QLineSeries()
        self.cpu_chart.addSeries(self.cpu_series)
        self.cpu_series.attachAxis(self.cpu_chart.axes(Qt.Horizontal)[0])
        self.cpu_series.attachAxis(self.cpu_chart.axes(Qt.Vertical)[0])

        self.cpu_chart_view = QChartView(self.cpu_chart)
        self.cpu_chart_view.setFixedHeight(150)
        cpu_section.add_chart(self.cpu_chart_view)

        layout.addWidget(cpu_section)

        # Memory Section
        memory_section = PerformanceWidget("Память")
        self.memory_meter = ResourceMeter()
        self.memory_info_label = QLabel()
        memory_section.add_meter(self.memory_meter)
        memory_section.add_info(self.memory_info_label)

        self.memory_chart = create_chart()
        self.memory_series = QLineSeries()
        self.memory_chart.addSeries(self.memory_series)
        self.memory_series.attachAxis(self.memory_chart.axes(Qt.Horizontal)[0])
        self.memory_series.attachAxis(self.memory_chart.axes(Qt.Vertical)[0])

        self.memory_chart_view = QChartView(self.memory_chart)
        self.memory_chart_view.setFixedHeight(150)
        memory_section.add_chart(self.memory_chart_view)

        layout.addWidget(memory_section)

        # Disk Section
        disk_section = PerformanceWidget("Диск")
        self.disk_meter = ResourceMeter()
        self.disk_info_label = QLabel()
        disk_section.add_meter(self.disk_meter)
        disk_section.add_info(self.disk_info_label)

        self.disk_chart = create_chart()
        self.disk_series = QLineSeries()
        self.disk_chart.addSeries(self.disk_series)
        self.disk_series.attachAxis(self.disk_chart.axes(Qt.Horizontal)[0])
        self.disk_series.attachAxis(self.disk_chart.axes(Qt.Vertical)[0])

        self.disk_chart_view = QChartView(self.disk_chart)
        self.disk_chart_view.setFixedHeight(150)
        disk_section.add_chart(self.disk_chart_view)

        layout.addWidget(disk_section)

        # Network Section (особые настройки для сети)
        network_section = PerformanceWidget("Сеть")
        self.network_meter = ResourceMeter()
        self.network_info_label = QLabel()
        network_section.add_meter(self.network_meter)
        network_section.add_info(self.network_info_label)

        self.network_chart = QChart()
        self.network_chart.setBackgroundVisible(False)
        self.network_chart.legend().hide()
        self.network_chart.setMargins(QMargins(0, 0, 0, 0))
        self.network_chart.layout().setContentsMargins(0, 0, 0, 0)

        # Ось X (время)
        axis_x = QValueAxis()
        axis_x.setRange(0, 60)
        axis_x.setTickCount(7)
        axis_x.setLabelFormat("%.0f")
        axis_x.setTitleText("Seconds ago")
        self.network_chart.addAxis(axis_x, Qt.AlignBottom)

        # Ось Y (значения)
        axis_y = QValueAxis()
        axis_y.setRange(0, 3)  # Начальный диапазон для сети
        axis_y.setTitleText("Mbps")
        self.network_chart.addAxis(axis_y, Qt.AlignLeft)

        self.network_series = QLineSeries()
        self.network_chart.addSeries(self.network_series)
        self.network_series.attachAxis(axis_x)
        self.network_series.attachAxis(axis_y)

        self.network_chart_view = QChartView(self.network_chart)
        self.network_chart_view.setFixedHeight(150)
        network_section.add_chart(self.network_chart_view)

        layout.addWidget(network_section)

        layout.addStretch(1)
        self.tab_widget.addTab(scroll_area, "Производительность")


    def init_timer(self):
        """Инициализирует таймер для обновления данных"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_all)
        self.timer.start(1000)  # Обновление каждую секунду

    def update_all(self):
        """Обновляет все данные в интерфейсе"""
        # Обновление данных системы
        cpu_usage, memory_usage = self.system_monitor.update_stats()
        self.system_panel.update_stats(cpu_usage, memory_usage)

        # Обновление данных процессов
        gui_procs, bg_procs = self.process_controller.get_processes()
        self.source_model.update_data(gui_procs, bg_procs)

        # Обновление вкладки производительности
        self.update_performance_tab(cpu_usage, memory_usage)

    def update_performance_tab(self, cpu_usage, memory_usage):
        """Обновляет данные на вкладке производительности"""
        # Обновление CPU
        self.cpu_meter.set_value(cpu_usage)
        cpu_info = self.system_monitor.get_cpu_info()
        self.cpu_info_label.setText(
            f"Использование: {cpu_usage}%\n"
            f"Процессор: {cpu_info['name']}\n"
            f"Базовая скорость: {cpu_info['base_speed']} GHz\n"
            f"Ядра: {cpu_info['cores']} (логических: {cpu_info['logical']})"
        )
        self.update_chart(self.cpu_series, cpu_usage, "CPU Usage (%)")

        memory_info = self.system_monitor.get_memory_info()
        self.memory_meter.set_value(memory_usage)



        self.memory_info_label.setText(
            f"Использовано: {memory_info['used']:.1f} GB из {memory_info['total']:.1f} GB ({memory_usage}%)\n"
            f"Доступно: {memory_info['available']:.1f} GB\n"
            f"Кэшировано: {memory_info['cached']:.1f} GB\n"

        )
        self.update_chart(self.memory_series, memory_usage, "Memory Usage (%)")

        # Обновление диска
        disk_info = self.system_monitor.get_disk_info()
        disk_usage = disk_info['usage_percent']
        self.disk_meter.set_value(disk_usage)
        self.disk_info_label.setText(
            f"Активное время: {disk_info['active_time']}%\n"
            f"Среднее время отклика: {disk_info['response_time']} ms\n"
            f"Скорость чтения: {disk_info['read_speed']:.1f} MB/s\n"
            f"Скорость записи: {disk_info['write_speed']:.1f} MB/s"
        )
        self.update_chart(self.disk_series, disk_info['active_time'], "Disk Active Time (%)")

        # Обновление сети
        network_info = self.system_monitor.get_network_info()
        self.network_meter.set_value(network_info['usage_percent'])
        self.network_info_label.setText(
            f"Отправлено: {network_info['sent']:.1f} MB\n"
            f"Получено: {network_info['received']:.1f} MB\n"
            f"Скорость отправки: {network_info['send_speed']:.1f} Mbps\n"
            f"Скорость приема: {network_info['receive_speed']:.1f} Mbps"
        )
        self.update_chart(self.network_series, network_info['usage_percent'], "Network Usage (%)")



    def update_chart(self, series, new_value, title):
        """Обновляет график новым значением"""
        # Добавляем новую точку
        current_time = series.count()
        series.append(current_time, new_value)

        # Если точек больше 60, удаляем самую старую
        if series.count() > 60:
            series.remove(0)
            # Сдвигаем оставшиеся точки назад
            for i in range(series.count()):
                point = series.pointsVector()[i]
                series.replace(i, QPointF(i, point.y()))

        # Обновляем диапазон оси X
        chart = series.chart()
        axis_x = chart.axes(Qt.Horizontal)[0]
        axis_x.setRange(max(0, series.count() - 60), max(60, series.count()))

        # Для сетевого графика динамически обновляем масштаб
        if title == "Network Usage (Mbps)":
            current_max = max(point.y() for point in series.pointsVector()) if series.count() > 0 else 10
            axis_y = chart.axes(Qt.Vertical)[0]
            axis_y.setRange(0, max(10, current_max * 1.2))  # 20% запас сверху


