from PyQt5.QtWidgets import QTableView, QHeaderView, QMenu, QMessageBox, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QCursor

from PyQt5.QtWidgets import QTableView, QHeaderView, QMenu, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QCursor


class ProcessTableView(QTableView):
    """Кастомное представление таблицы процессов с контекстным меню"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process_controller = None
        self.setup_ui()

    def setup_ui(self):
        self.setup_basic_ui()
        self.setup_context_menu()

    def setup_basic_ui(self):
        """Базовая настройка таблицы"""
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(QHeaderView.Stretch)
        # Настройка ширины колонок

        self.setColumnWidth(0, 30)
        self.setColumnWidth(2, 80)
        self.setColumnWidth(3, 80)
        self.setColumnWidth(4, 80)
        self.setColumnWidth(5, 100)
        self.setColumnWidth(6, 150)

    def setup_context_menu(self):
        """Настройка контекстного меню"""
        self._context_menu = QMenu(self)

        end_action = self._context_menu.addAction("Завершить процесс")
        end_action.triggered.connect(self._terminate_selected_process)

        kill_action = self._context_menu.addAction("Принудительно завершить")
        kill_action.triggered.connect(self._kill_selected_process)

        self.customContextMenuRequested.connect(self._show_context_menu)

    def set_process_controller(self, controller):
        """Устанавливает контроллер процессов"""
        if controller is None:
            raise ValueError("Process controller cannot be None")
        self._process_controller = controller

    def _show_context_menu(self, pos):
        """Показывает контекстное меню"""
        if self._context_menu:
            self._context_menu.exec_(self.viewport().mapToGlobal(pos))

    def _get_selected_pid(self):
        """Возвращает PID выбранного процесса"""
        selected = self.selectedIndexes()
        if not selected:
            return -1

        # Получаем PID из колонки 2 выбранной строки
        pid_index = selected[0].siblingAtColumn(2)
        if not pid_index.isValid():
            return -1

        try:
            return int(pid_index.data())
        except (ValueError, TypeError):
            return -1

    def _terminate_selected_process(self):
        """Завершает выбранный процесс"""
        pid = self._get_selected_pid()
        if pid <= 0:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить PID процесса")
            return

        if not self._process_controller:
            QMessageBox.critical(self, "Ошибка", "Контроллер процессов не инициализирован")
            return

        try:
            success, message = self._process_controller.terminate_process(pid)
            QMessageBox.information(self, "Результат", message)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка завершения процесса: {str(e)}")

    def _kill_selected_process(self):
        """Принудительно завершает процесс"""
        pid = self._get_selected_pid()
        if pid <= 0:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить PID процесса")
            return

        if not self._process_controller:
            QMessageBox.critical(self, "Ошибка", "Контроллер процессов не инициализирован")
            return

        try:
            success, message = self._process_controller.kill_process(pid)
            QMessageBox.information(self, "Результат", message)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка принудительного завершения: {str(e)}")