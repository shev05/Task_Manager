from PyQt5.QtWidgets import QStyle
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Импортируем наш логгер
from utils.loggerService.logger import logger


class ProcessTableModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        logger.info("Инициализация ProcessTableModel.")
        self.setHorizontalHeaderLabels(["", "Имя", "PID", "ЦП", "Память", "Статус", "Пользователь"])
        self.process_icons = {}
        self.current_pids = set()

        # Загружаем стандартную иконку-шестерёнку
        self.default_icon = QIcon.fromTheme("system-run")  # Или другой подходящий вариант
        if self.default_icon.isNull():
            logger.warning("Не удалось загрузить иконку 'system-run'. Попытка использовать SP_ComputerIcon.")
            # Если тема не предоставляет иконку, создаём простую из ресурсов Qt
            self.default_icon = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
            if self.default_icon.isNull():
                 logger.critical("Не удалось загрузить стандартную иконку SP_ComputerIcon.")

        logger.info("ProcessTableModel инициализирована.")


    def update_data(self, gui_procs, bg_procs):
        """Обновляет данные модели на основе списков процессов"""
        # logger.debug("Начало обновления данных модели процессов.")
        new_pids = {str(proc['pid']) for proc in gui_procs + bg_procs}

        # Удаление исчезнувших процессов
        self.remove_disappeared_processes(new_pids)

        # Обновление или добавление процессов
        all_procs = gui_procs + bg_procs
        existing_rows = self.get_existing_rows()

        for proc in all_procs:
            pid = str(proc['pid'])
            if pid in existing_rows:
                self.update_row(existing_rows[pid], proc)
            else:
                self.add_row(proc, pid in {str(p['pid']) for p in gui_procs})

        self.current_pids = new_pids
        # logger.debug("Данные модели процессов обновлены.")


    def remove_disappeared_processes(self, new_pids):
        """Удаляет процессы, которые больше не существуют"""
        # logger.debug("Проверка и удаление исчезнувших процессов.")
        removed_count = 0
        for row in reversed(range(self.rowCount())):
            if self.item(row, 2).text() not in new_pids:
                pid_to_remove = self.item(row, 2).text()
                self.removeRow(row)
                # logger.debug(f"Удален процесс с PID {pid_to_remove}.")
                removed_count += 1
        # if removed_count > 0:
            # logger.info(f"Удалено {removed_count} исчезнувших процессов.")


    def get_existing_rows(self):
        """Возвращает словарь {pid: row} для существующих процессов"""
        # logger.debug("Получение словаря существующих строк.")
        existing_rows = {self.item(row, 2).text(): row for row in range(self.rowCount())}
        # logger.debug(f"Найдено {len(existing_rows)} существующих процессов в модели.")
        return existing_rows

    def add_row(self, proc, is_app):
        """Добавляет новую строку с информацией о процессе"""
        pid = proc.get('pid', 0)
        name = proc.get('name', 'N/A')
        # logger.debug(f"Попытка добавить процесс PID: {pid}, Имя: {name}.")
        try:
            icon_item = self.create_icon_item(name if is_app else None)
            name_item = QStandardItem(name)
            pid_item = QStandardItem(str(pid))
            cpu_item = QStandardItem(f"{proc.get('cpu', 0):.1f}%")
            mem_item = QStandardItem(f"{proc.get('memory', 0):.1f}%")
            status_item = QStandardItem(proc.get('status', 'N/A'))
            user_item = QStandardItem(proc.get('user', 'N/A'))

            # Центрирование текста для числовых колонок
            for item in [pid_item, cpu_item, mem_item, status_item, user_item]:
                item.setTextAlignment(Qt.AlignCenter)

            # Добавление в начало для GUI процессов, в конец для фоновых
            if is_app:
                self.insertRow(0, [icon_item, name_item, pid_item, cpu_item, mem_item, status_item, user_item])
                logger.debug(f"Добавлен GUI процесс PID: {pid}, Имя: {name}.")
            else:
                self.appendRow([icon_item, name_item, pid_item, cpu_item, mem_item, status_item, user_item])
                # logger.debug(f"Добавлен фоновый процесс PID: {pid}, Имя: {name}.")

        except Exception as e:
            logger.error(f"Ошибка при добавлении процесса PID {pid} ({name}): {e}")


    def create_icon_item(self, process_name):
        """Создает элемент с иконкой процесса"""
        icon_item = QStandardItem()
        if process_name:
            icon = self.get_process_icon(process_name)
            if not icon.isNull():
                icon_item.setIcon(icon)
                # logger.debug(f"Иконка для '{process_name}' найдена и установлена.")
            else:
                # Устанавливаем иконку-шестерёнку по умолчанию
                icon_item.setIcon(self.default_icon)
                # logger.debug(f"Иконка для '{process_name}' не найдена, использована иконка по умолчанию.")
            icon_item.setText("")  # Убираем текст полностью
        else:
            # Для процессов без имени тоже используем шестерёнку
            icon_item.setIcon(self.default_icon)
            icon_item.setText("")
            # logger.debug("Иконка для процесса без имени установлена по умолчанию.")
        return icon_item

    def get_process_icon(self, process_name):
        """Возвращает иконку для процесса по его имени"""
        if process_name in self.process_icons:
            # logger.debug(f"Иконка для '{process_name}' найдена в кэше.")
            return self.process_icons[process_name]

        # Расширенное сопоставление имен процессов с иконками
        icon_mapping = {
            'chrome': 'google-chrome',
            'firefox': 'firefox',
            'nautilus': 'system-file-manager',
            'code': 'visual-studio-code',
            'pycharm': 'pycharm',
            'gedit': 'accessories-text-editor',
            'libreoffice': 'libreoffice',
            'thunderbird': 'thunderbird',
            'discord': 'discord',
            'spotify': 'spotify-client',
            'telegram': 'telegram-desktop',
            'slack': 'slack',
            'python': 'python',
            'python3': 'python',
            'python3.12': 'python',
            'bash': 'utilities-terminal',
            'zsh': 'utilities-terminal',
            'ssh': 'network-wired',
            'systemd': 'system-run',
            'dbus': 'system-run',
            'pipewire': 'audio-card',
            'pulseaudio': 'audio-card',
            'gnome': 'gnome',
            'kde': 'kde',
            'xdg': 'system-run'
        }

        name_lower = process_name.lower()
        for key, icon_name in icon_mapping.items():
            if key in name_lower:
                try:
                    icon = QIcon.fromTheme(icon_name)
                    if not icon.isNull():
                        self.process_icons[process_name] = icon
                        # logger.debug(f"Иконка '{icon_name}' для '{process_name}' найдена в теме.")
                        return icon
                except Exception as e:
                    logger.warning(f"Ошибка при попытке загрузить иконку '{icon_name}' для '{process_name}': {e}")
                    continue

        # Если иконка не найдена, возвращаем пустую иконку
        # (метод create_icon_item подставит шестерёнку)
        # logger.debug(f"Иконка для '{process_name}' не найдена по сопоставлению.")
        return QIcon()

    def update_row(self, row, proc):
        """Обновляет данные в существующей строке"""
        pid = self.item(row, 2).text()
        # logger.debug(f"Попытка обновить процесс PID: {pid}.")
        try:
            self.item(row, 3).setText(f"{proc.get('cpu', 0):.1f}%")
            self.item(row, 4).setText(f"{proc.get('memory', 0):.1f}%")
            self.item(row, 5).setText(proc.get('status', 'N/A'))
            # logger.debug(f"Процесс PID {pid} обновлен успешно.")
        except Exception as e:
            logger.error(f"Ошибка при обновлении процесса PID {pid}: {e}")


class ProcessSortFilterProxyModel(QSortFilterProxyModel):
    """Прокси-модель для сортировки и фильтрации процессов"""

    def __init__(self):
        super().__init__()
        logger.info("Инициализация ProcessSortFilterProxyModel.")
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        logger.info("ProcessSortFilterProxyModel инициализирована.")


    def lessThan(self, left, right):
        """Кастомная сортировка для числовых колонок"""
        column = left.column()

        # Специальная обработка для колонок с процентами (ЦП и Память)
        if column in (3, 4):  # Колонки ЦП и Памяти
            try:
                left_value = float(left.data().replace('%', ''))
                right_value = float(right.data().replace('%', ''))
                # logger.debug(f"Сортировка числовых значений в колонке {column}.")
                return left_value < right_value
            except ValueError:
                logger.warning(f"Ошибка преобразования значений в колонке {column} для сортировки.")
                # Fallback to default comparison if conversion fails
                pass

        # Стандартная сортировка для остальных колонок
        # logger.debug(f"Стандартная сортировка в колонке {column}.")
        return super().lessThan(left, right)