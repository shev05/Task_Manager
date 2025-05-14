from PyQt5.QtWidgets import QTableView, QHeaderView, QMenu, QMessageBox
from PyQt5.QtCore import Qt

# Импортируем наш логгер
from utils.loggerService.logger import logger


class ProcessTableView(QTableView):
    """Кастомное представление таблицы процессов с контекстным меню"""

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Инициализация ProcessTableView.")
        self._process_controller = None
        self.setup_ui()
        logger.info("ProcessTableView инициализирована.")


    def setup_ui(self):
        logger.debug("Настройка UI ProcessTableView.")
        self.setup_basic_ui()
        self.setup_context_menu()
        logger.debug("UI ProcessTableView настроена.")


    def setup_basic_ui(self):
        """Базовая настройка таблицы"""
        logger.debug("Настройка базового UI ProcessTableView.")
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
        logger.debug("Базовый UI ProcessTableView настроен.")


    def setup_context_menu(self):
        """Настройка контекстного меню"""
        logger.debug("Настройка контекстного меню ProcessTableView.")
        self._context_menu = QMenu(self)

        end_action = self._context_menu.addAction("Завершить процесс")
        end_action.triggered.connect(self._terminate_selected_process)

        kill_action = self._context_menu.addAction("Принудительно завершить")
        kill_action.triggered.connect(self._kill_selected_process)

        self.customContextMenuRequested.connect(self._show_context_menu)
        logger.debug("Контекстное меню ProcessTableView настроено.")


    def set_process_controller(self, controller):
        """Устанавливает контроллер процессов"""
        logger.debug("Установка контроллера процессов в ProcessTableView.")
        if controller is None:
            logger.error("Попытка установить None в качестве контроллера процессов.")
            raise ValueError("Process controller cannot be None")
        self._process_controller = controller
        logger.debug("Контроллер процессов установлен.")


    def _show_context_menu(self, pos):
        """Показывает контекстное меню"""
        logger.debug(f"Запрос контекстного меню в позиции {pos.x()}, {pos.y()}.")
        if self._context_menu:
            self._context_menu.exec_(self.viewport().mapToGlobal(pos))
            logger.debug("Контекстное меню показано.")


    def _get_selected_pid(self):
        """Возвращает PID выбранного процесса"""
        selected = self.selectedIndexes()
        if not selected:
            logger.warning("Попытка получить PID выбранного процесса, но ни один процесс не выбран.")
            return -1

        # Получаем PID из колонки 2 выбранной строки
        pid_index = selected[0].siblingAtColumn(2)
        if not pid_index.isValid():
            logger.warning("Недействительный индекс PID выбранного процесса.")
            return -1

        try:
            pid = int(pid_index.data())
            logger.debug(f"Получен PID выбранного процесса: {pid}")
            return pid
        except (ValueError, TypeError) as e:
            logger.error(f"Ошибка при преобразовании PID выбранного процесса в число: {e}")
            return -1

    def _terminate_selected_process(self):
        """Завершает выбранный процесс"""
        pid = self._get_selected_pid()
        if pid <= 0:
            # Логгирование ошибки уже происходит в _get_selected_pid
            QMessageBox.warning(self, "Ошибка", "Не удалось получить PID процесса")
            return

        if not self._process_controller:
            logger.critical("Контроллер процессов не инициализирован при попытке завершить процесс.")
            QMessageBox.critical(self, "Ошибка", "Контроллер процессов не инициализирован")
            return

        logger.info(f"Попытка завершить процесс с PID: {pid} из контекстного меню.")
        try:
            success, message = self._process_controller.terminate_process(pid)
            # Логгирование успеха/ошибки происходит внутри terminate_process
            QMessageBox.information(self, "Результат", message)
        except Exception as e:
            logger.error(f"Неожиданная ошибка при вызове terminate_process для PID {pid}: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка завершения процесса: {str(e)}")

    def _kill_selected_process(self):
        """Принудительно завершает процесс"""
        pid = self._get_selected_pid()
        if pid <= 0:
            # Логгирование ошибки уже происходит в _get_selected_pid
            QMessageBox.warning(self, "Ошибка", "Не удалось получить PID процесса")
            return

        if not self._process_controller:
            logger.critical("Контроллер процессов не инициализирован при попытке принудительно завершить процесс.")
            QMessageBox.critical(self, "Ошибка", "Контроллер процессов не инициализирован")
            return

        logger.warning(f"Попытка принудительно завершить процесс с PID: {pid} из контекстного меню.")
        try:
            success, message = self._process_controller.kill_process(pid)
            # Логгирование успеха/ошибки происходит внутри kill_process
            QMessageBox.information(self, "Результат", message)
        except Exception as e:
            logger.error(f"Неожиданная ошибка при вызове kill_process для PID {pid}: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка принудительного завершения: {str(e)}")