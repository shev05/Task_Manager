# main_window.py

import sys
import psutil

from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtCore import QTimer, Qt, QMargins, QPointF
# Добавили QGridLayout
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QTabWidget,
                             QLabel, QSizePolicy, QScrollArea, QGridLayout)
from PyQt5.QtGui import QColor, QPen # Импортируем QColor и QPen

from controllers.process_controller import ProcessController
from models.process_model import ProcessTableModel
from models.system_monitor import SystemMonitor
# CoreUsageWidget больше не используется для основного графика ЦП, но может остаться если нужен в другом месте
from views.widgets.performance_widget import PerformanceWidget, ResourceMeter, CoreUsageWidget
from views.widgets.process_table import ProcessTableView
from views.widgets.system_panel import SystemPanel


class TaskManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Диспетчер задач")
        self.setGeometry(100, 100, 1000, 700)

        self.source_model = ProcessTableModel()
        self.system_monitor = SystemMonitor()
        self.process_controller = ProcessController()

        # Список для хранения серий каждого ядра для единого графика ЦП
        self.cpu_core_series = []
        self.cpu_chart = None # Будет инициализирован в create_performance_tab

        # Список для хранения меток с процентами загрузки ядер
        self.cpu_core_labels = []

        # Список цветов для графиков ядер
        self.core_colors = [
            QColor(0, 150, 0),    # Зеленый
            QColor(255, 0, 0),    # Красный
            QColor(0, 0, 255),    # Синий
            QColor(255, 165, 0),  # Оранжевый
            QColor(128, 0, 128),  # Фиолетовый
            QColor(0, 128, 128),  # Бирюзовый
            QColor(255, 192, 203),# Розовый
            QColor(100, 149, 237),# Cornflower Blue
            QColor(218, 165, 32), # Goldenrod
            QColor(64, 224, 208), # Turquoise
            QColor(138, 43, 226), # BlueViolet
            QColor(255, 99, 71),  # Tomato
        ] # Добавьте больше цветов при необходимости

        self.init_ui()
        self.init_timer()

    def init_ui(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.create_process_tab()
        self.create_performance_tab()

        self.setCentralWidget(self.tab_widget)

    def create_process_tab(self):
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

        # CPU Section
        cpu_section = PerformanceWidget("Процессор")

        # Контейнер для информации о процессоре и легенды ядер
        cpu_info_and_legend_layout = QVBoxLayout()

        # Добавляем информацию о процессоре
        self.cpu_info_label = QLabel()
        cpu_info_and_legend_layout.addWidget(self.cpu_info_label)

        # Создаем сетку для легенды ядер (цветные квадраты + проценты)
        cores_legend_grid = QGridLayout()
        cores_legend_grid.setSpacing(5) # Устанавливаем отступы между элементами сетки

        num_logical_cores = psutil.cpu_count(logical=True)
        cores_per_row = 4 # Количество элементов легенды на строку
        self.cpu_core_labels.clear() # Очищаем список на случай повторного вызова

        for i in range(num_logical_cores):
            # Создаем виджет для цветного квадрата
            color_square = QLabel()
            color_square.setFixedSize(15, 15) # Фиксированный размер для квадрата
            color_square.setStyleSheet(f"background-color: {self.core_colors[i % len(self.core_colors)].name()}; border: 1px solid black;") # Устанавливаем цвет и рамку

            # Создаем метку для текста легенды (например, "ЦП 1: 0.0%")
            usage_label = QLabel(f"ЦП {i + 1}: 0.0%")
            self.cpu_core_labels.append(usage_label) # Сохраняем ссылку на метку

            row = i // cores_per_row
            col = i % cores_per_row * 2 # Удваиваем колонку, чтобы добавить место для текста

            cores_legend_grid.addWidget(color_square, row, col)
            cores_legend_grid.addWidget(usage_label, row, col + 1)

        # Добавляем сетку с легендой ядер в макет информации
        cpu_info_and_legend_layout.addLayout(cores_legend_grid)
        cpu_info_and_legend_layout.addStretch(1) # Растяжка после легенды


        # Удалим существующие элементы из info_container_layout перед добавлением нового макета
        while cpu_section.info_container_layout.count():
            item = cpu_section.info_container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            del item

        # Добавляем вертикальный макет информации и легенды в горизонтальный макет информации PerformanceWidget
        cpu_section.info_container_layout.addLayout(cpu_info_and_legend_layout)
        cpu_section.info_container_layout.addStretch(1) # Растяжка после этого блока


        # Создаем единый график для всех ядер ЦП
        self.cpu_chart = QChart()
        self.cpu_chart.setBackgroundVisible(False)
        # Увеличиваем левый отступ для оси Y
        self.cpu_chart.setMargins(QMargins(30, 0, 0, 0)) # Увеличено левый отступ
        self.cpu_chart.layout().setContentsMargins(0, 0, 0, 0)
        self.cpu_chart.legend().hide() # Скрываем стандартную легенду, т.к. создаем свою

        # Оси для графика ЦП
        axis_x = QValueAxis()
        axis_x.setRange(0, 60)
        axis_x.setTickCount(7)
        axis_x.setLabelFormat("%.0f")
        axis_x.setTitleText("Seconds ago")
        self.cpu_chart.addAxis(axis_x, Qt.AlignBottom)

        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setTitleText("Usage (%)")
        self.cpu_chart.addAxis(axis_y, Qt.AlignLeft)

        # Создаем серии для каждого ядра с толстыми линиями
        self.cpu_core_series.clear() # Очищаем список на случай повторного вызова
        for i in range(num_logical_cores):
            series = QLineSeries()
            series.setName(f"ЦП {i + 1}") # Имя серии (хоть и скрыто, может быть полезно)
            pen = QPen(self.core_colors[i % len(self.core_colors)])
            pen.setWidth(2) # Устанавливаем толщину линии
            series.setPen(pen)
            self.cpu_chart.addSeries(series)
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
            self.cpu_core_series.append(series)


        cpu_chart_view = QChartView(self.cpu_chart)
        cpu_chart_view.setFixedHeight(200) # Увеличиваем высоту графика ЦП
        cpu_section.add_chart_view(cpu_chart_view) # Добавляем график в charts_layout

        layout.addWidget(cpu_section)


        # Memory Section (остается без изменений)
        memory_section = PerformanceWidget("Память")

        self.memory_meter = ResourceMeter()
        self.memory_meter.setFixedSize(80, 80)
        self.memory_info_label = QLabel()
        memory_section.info_container_layout.addWidget(self.memory_meter)
        memory_section.info_container_layout.addWidget(self.memory_info_label)
        memory_section.info_container_layout.addStretch(1)

        memory_chart = QChart()
        memory_chart.setBackgroundVisible(False)
        memory_chart.legend().hide()
        # Увеличиваем нижний и левый отступ для осей X и Y на графике памяти
        memory_chart.setMargins(QMargins(30, 0, 0, 10)) # Увеличено левый и нижний отступ
        memory_chart.layout().setContentsMargins(0, 0, 0, 0)

        axis_x = QValueAxis()
        axis_x.setRange(0, 60)
        axis_x.setTickCount(7)
        axis_x.setLabelFormat("%.0f")
        axis_x.setTitleText("Seconds ago")
        memory_chart.addAxis(axis_x, Qt.AlignBottom)

        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setTitleText("Usage (%)")
        memory_chart.addAxis(axis_y, Qt.AlignLeft)

        self.memory_series = QLineSeries()
        # Устанавливаем толщину линии для графика памяти
        pen_mem = QPen(QColor(0, 0, 255)) # Цвет синий, например
        pen_mem.setWidth(2)
        self.memory_series.setPen(pen_mem)
        memory_chart.addSeries(self.memory_series)
        self.memory_series.attachAxis(axis_x)
        self.memory_series.attachAxis(axis_y)

        memory_chart_view = QChartView(memory_chart)
        memory_chart_view.setFixedHeight(150)
        memory_section.add_chart_view(memory_chart_view)

        layout.addWidget(memory_section)

        # Disk Section
        disk_section = PerformanceWidget("Диск")

        self.disk_meter = ResourceMeter()
        self.disk_meter.setFixedSize(80, 80)
        self.disk_info_label = QLabel()
        disk_section.info_container_layout.addWidget(self.disk_meter)
        disk_section.info_container_layout.addWidget(self.disk_info_label)
        disk_section.info_container_layout.addStretch(1)


        disk_chart = QChart()
        disk_chart.setBackgroundVisible(False)
        #disk_chart.legend().hide() # Легенда для диска остается видимой
        # Увеличиваем нижний и левый отступ для осей X и Y на графике диска
        disk_chart.setMargins(QMargins(30, 0, 0, 10)) # Увеличено левый и нижний отступ
        disk_chart.layout().setContentsMargins(0, 0, 0, 0)

        axis_x = QValueAxis()
        axis_x.setRange(0, 60)
        axis_x.setTickCount(7)
        axis_x.setLabelFormat("%.0f")
        axis_x.setTitleText("Seconds ago")
        disk_chart.addAxis(axis_x, Qt.AlignBottom)

        axis_y = QValueAxis()
        # Увеличиваем диапазон оси Y для диска
        axis_y.setRange(0, 200) # Увеличено с 50 до 200
        # Изменяем текст заголовка оси Y
        axis_y.setTitleText("MB/s") # Изменено с "Speed (MB/s)"
        disk_chart.addAxis(axis_y, Qt.AlignLeft)

        self.disk_read_series = QLineSeries()
        self.disk_write_series = QLineSeries()
        self.disk_read_series.setName("Чтение")
        self.disk_write_series.setName("Запись")

        # Устанавливаем толщину линий для графика диска
        pen_read = QPen(QColor(0, 150, 0)) # Зеленый для чтения
        pen_read.setWidth(2)
        self.disk_read_series.setPen(pen_read)

        pen_write = QPen(QColor(255, 0, 0)) # Красный для записи
        pen_write.setWidth(2)
        self.disk_write_series.setPen(pen_write)


        disk_chart.addSeries(self.disk_read_series)
        disk_chart.addSeries(self.disk_write_series)
        self.disk_read_series.attachAxis(axis_x)
        self.disk_read_series.attachAxis(axis_y)
        self.disk_write_series.attachAxis(axis_x)
        self.disk_write_series.attachAxis(axis_y)
        disk_chart.legend().setVisible(True)

        disk_chart_view = QChartView(disk_chart)
        disk_chart_view.setFixedHeight(200) # Увеличено с 150 до 200
        disk_section.add_chart_view(disk_chart_view)

        layout.addWidget(disk_section)

        # Network Section
        network_section = PerformanceWidget("Сеть")

        # Метр для сети (можно убрать или изменить)
        # self.network_meter = ResourceMeter()
        # self.network_meter.setFixedSize(80, 80)
        # network_section.info_container_layout.addWidget(self.network_meter)

        self.network_info_label = QLabel()
        network_section.info_container_layout.addWidget(self.network_info_label)
        network_section.info_container_layout.addStretch(1)


        network_chart = QChart()
        network_chart.setBackgroundVisible(False)
        #network_chart.legend().hide() # Легенда для сети остается видимой
        # Увеличиваем нижний и левый отступ для осей X и Y на графике сети
        network_chart.setMargins(QMargins(30, 0, 0, 10)) # Увеличено левый и нижний отступ
        network_chart.layout().setContentsMargins(0, 0, 0, 0)


        axis_x = QValueAxis()
        axis_x.setRange(0, 60)
        axis_x.setTickCount(7)
        axis_x.setLabelFormat("%.0f")
        axis_x.setTitleText("Seconds ago")
        network_chart.addAxis(axis_x, Qt.AlignBottom)

        axis_y = QValueAxis()
        axis_y.setRange(0, 5) # Начальный диапазон для скорости сети в Mbps
        # Изменяем текст заголовка оси Y
        axis_y.setTitleText("Mbps") # Изменено с "Speed (Mbps)"
        network_chart.addAxis(axis_y, Qt.AlignLeft)

        self.network_sent_series = QLineSeries()
        self.network_received_series = QLineSeries()
        self.network_sent_series.setName("Отправка")
        self.network_received_series.setName("Получение")

        # Устанавливаем толщину линий для графика сети
        pen_sent = QPen(QColor(0, 0, 255)) # Синий для отправки
        pen_sent.setWidth(2)
        self.network_sent_series.setPen(pen_sent)

        pen_recv = QPen(QColor(255, 165, 0)) # Оранжевый для получения
        pen_recv.setWidth(2)
        self.network_received_series.setPen(pen_recv)


        network_chart.addSeries(self.network_sent_series)
        network_chart.addSeries(self.network_received_series)
        self.network_sent_series.attachAxis(axis_x)
        self.network_sent_series.attachAxis(axis_y)
        self.network_received_series.attachAxis(axis_x)
        self.network_received_series.attachAxis(axis_y)
        network_chart.legend().setVisible(True)

        network_chart_view = QChartView(network_chart)
        network_chart_view.setFixedHeight(200) # Увеличено с 150 до 200
        network_section.add_chart_view(network_chart_view)

        layout.addWidget(network_section)

        layout.addStretch(1)
        self.tab_widget.addTab(scroll_area, "Производительность")


    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_all)
        self.timer.start(1000)

    def update_all(self):
        # Вызываем update_stats, чтобы обновить внутренние данные system_monitor,
        # включая загрузку ядер.
        self.system_monitor.update_stats()

        # Обновление панели сверху (общая загрузка ЦП и Памяти)
        self.system_panel.update_stats(self.system_monitor.cpu_percent, self.system_monitor.mem_percent)

        gui_procs, bg_procs = self.process_controller.get_processes()
        self.source_model.update_data(gui_procs, bg_procs)

        self.update_performance_tab()

    def update_performance_tab(self):
        # Обновление информации о CPU (общая информация о процессоре)
        cpu_info = self.system_monitor.get_cpu_info()
        self.cpu_info_label.setText(
            f"Процессор: {cpu_info['name']}\n"
            # Удалена строка с базовой скоростью
            f"Ядра: {cpu_info['cores']} (логических: {cpu_info['logical']})"
        )

        # Обновление единого графика ядер ЦП и меток процентов
        cpu_per_core = self.system_monitor.get_cpu_per_core()
        # Убедимся, что количество данных по ядрам соответствует количеству серий и меток
        if len(cpu_per_core) == len(self.cpu_core_series) and len(cpu_per_core) == len(self.cpu_core_labels):
            for i, core_usage in enumerate(cpu_per_core):
                 # Обновляем серию графика
                self.update_chart_series(self.cpu_core_series[i], core_usage, is_cpu=True)
                # Обновляем метку с процентом загрузки
                self.cpu_core_labels[i].setText(f"ЦП {i + 1}: {core_usage:.1f}%")
        # else:
            # print("Warning: Mismatch in number of CPU cores, series, or labels.")


        # Обновление информации о памяти
        memory_info = self.system_monitor.get_memory_info()
        memory_usage = self.system_monitor.mem_percent
        self.memory_meter.set_value(memory_usage)
        self.memory_info_label.setText(
            f"Использовано: {memory_info['used']:.1f} GB из {memory_info['total']:.1f} GB\n"
            f"({memory_usage:.1f}%)\n"
            f"Доступно: {memory_info['available']:.1f} GB\n"
            f"Кэшировано: {memory_info['cached']:.1f} GB"

        )
        self.update_chart_series(self.memory_series, memory_usage)

        # Обновление информации о диске
        disk_info = self.system_monitor.get_disk_info()
        disk_usage_percent = disk_info['usage_percent']
        self.disk_meter.set_value(disk_usage_percent)
        self.disk_info_label.setText(
            f"Свободно: {(100 - disk_usage_percent):.1f}%\n"
            f"Скорость чтения: {disk_info['read_speed']:.1f} MB/s\n"
            f"Скорость записи: {disk_info['write_speed']:.1f} MB/s"
        )
        self.update_chart_series(self.disk_read_series, disk_info['read_speed'], is_disk=True)
        self.update_chart_series(self.disk_write_series, disk_info['write_speed'], is_disk=True)


        # Обновление информации о сети
        network_info = self.system_monitor.get_network_info()
        # network_usage_percent = network_info['usage_percent'] # Использование метра для сети можно убрать
        # self.network_meter.set_value(network_usage_percent) # Закомментировано
        self.network_info_label.setText(
            f"Всего отправлено: {network_info['sent']:.1f} MB\n"
            f"Всего получено: {network_info['received']:.1f} MB\n"
            f"Скорость отправки: {network_info['send_speed']:.1f} Mbps\n"
            f"Скорость приема: {network_info['receive_speed']:.1f} Mbps"
        )
        self.update_chart_series(self.network_sent_series, network_info['send_speed'], is_network=True)
        self.update_chart_series(self.network_received_series, network_info['receive_speed'], is_network=True)


    # Модифицируем update_chart_series для поддержки диска, сети и ЦПУ по ядрам
    def update_chart_series(self, series: QLineSeries, new_value: float, is_network=False, is_disk=False, is_cpu=False):
        """Обновляет серию графика новым значением"""
        current_time = series.count()
        series.append(current_time, new_value)

        # Определяем, какой график нужно обновить
        if is_cpu:
             chart = self.cpu_chart
        elif is_network:
             chart = self.network_sent_series.chart()
        elif is_disk:
             chart = self.disk_read_series.chart()
        else:
             chart = self.memory_series.chart()


        if series.count() > 60:
            series.remove(0)
            # Сдвигаем оставшиеся точки по оси X
            for i in range(series.count()):
                point = series.pointsVector()[i]
                series.replace(i, QPointF(i, point.y()))

        # Обновляем диапазон оси X - всегда показываем последние 60 секунд
        axis_x = chart.axes(Qt.Horizontal)[0]
        # Устанавливаем диапазон от текущего времени минус 60 до текущего времени
        # Используем series.count() как текущее "время" в количестве точек
        max_x = series.count()
        min_x = max(0, max_x - 60)
        axis_x.setRange(min_x, max_x)


        axis_y = chart.axes(Qt.Vertical)[0]
        current_max = max(point.y() for point in series.pointsVector()) if series.count() > 0 else 1.0

        if is_network:
             axis_y.setRange(0, max(5.0, current_max * 1.2)) # Динамическое масштабирование для сети
        elif is_disk:
            axis_y.setRange(0, max(50.0, current_max * 1.2)) # Динамическое масштабирование для диска
        elif is_cpu:
             axis_y.setRange(0, 100) # Фиксированный диапазон для загрузки ЦПУ по ядрам
        else:
             axis_y.setRange(0, 100) # Фиксированный диапазон для загрузки памяти