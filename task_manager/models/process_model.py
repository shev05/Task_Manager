from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon


class ProcessTableModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        self.setHorizontalHeaderLabels(["", "Имя", "PID", "ЦП", "Память", "Статус", "Пользователь"])
        self.process_icons = {}
        self.current_pids = set()

    def update_data(self, gui_procs, bg_procs):
        """Обновляет данные модели на основе списков процессов"""
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

    def remove_disappeared_processes(self, new_pids):
        """Удаляет процессы, которые больше не существуют"""
        for row in reversed(range(self.rowCount())):
            if self.item(row, 2).text() not in new_pids:
                self.removeRow(row)

    def get_existing_rows(self):
        """Возвращает словарь {pid: row} для существующих процессов"""
        return {self.item(row, 2).text(): row for row in range(self.rowCount())}

    def add_row(self, proc, is_app):
        """Добавляет новую строку с информацией о процессе"""
        try:
            icon_item = self.create_icon_item(proc['name'] if is_app else None)
            name_item = QStandardItem(proc.get('name', 'N/A'))
            pid_item = QStandardItem(str(proc.get('pid', 0)))
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
            else:
                self.appendRow([icon_item, name_item, pid_item, cpu_item, mem_item, status_item, user_item])

        except Exception as e:
            print(f"Ошибка при добавлении процесса: {e}")

    def create_icon_item(self, process_name):
        """Создает элемент с иконкой процесса"""
        icon_item = QStandardItem()
        if process_name:
            icon = self.get_process_icon(process_name)
            if icon:
                icon_item.setIcon(icon)
            icon_item.setText("□" if not icon else "")
        return icon_item

    def update_row(self, row, proc):
        """Обновляет данные в существующей строке"""
        try:
            self.item(row, 3).setText(f"{proc.get('cpu', 0):.1f}%")
            self.item(row, 4).setText(f"{proc.get('memory', 0):.1f}%")
            self.item(row, 5).setText(proc.get('status', 'N/A'))
        except Exception as e:
            print(f"Ошибка при обновлении процесса: {e}")

    def get_process_icon(self, process_name):
        """Возвращает иконку для процесса по его имени"""
        if process_name in self.process_icons:
            return self.process_icons[process_name]

        # Сопоставление имен процессов с иконками из темы
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
            'zoom': 'zoom'
        }

        name_lower = process_name.lower()
        for key, icon_name in icon_mapping.items():
            if key in name_lower:
                try:
                    icon = QIcon.fromTheme(icon_name)
                    if not icon.isNull():
                        self.process_icons[process_name] = icon
                        return icon
                except:
                    continue

        return None


class ProcessSortFilterProxyModel(QSortFilterProxyModel):
    """Прокси-модель для сортировки и фильтрации процессов"""

    def __init__(self):
        super().__init__()
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)

    def lessThan(self, left, right):
        """Кастомная сортировка для числовых колонок"""
        column = left.column()

        # Специальная обработка для колонок с процентами (ЦП и Память)
        if column in (3, 4):  # Колонки ЦП и Памяти
            try:
                left_value = float(left.data().replace('%', ''))
                right_value = float(right.data().replace('%', ''))
                return left_value < right_value
            except ValueError:
                pass

        # Стандартная сортировка для остальных колонок
        return super().lessThan(left, right)