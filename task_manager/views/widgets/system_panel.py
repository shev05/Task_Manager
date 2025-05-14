from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar

# Импортируем наш логгер
from utils.loggerService.logger import logger


class SystemPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Инициализация SystemPanel.")
        self.cpu_progress = None
        self.mem_progress = None
        self.setup_ui()
        logger.info("SystemPanel инициализирована.")


    def setup_ui(self):
        logger.debug("Настройка UI SystemPanel.")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        cpu_label = QLabel("ЦП:")
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximum(100)
        self.cpu_progress.setTextVisible(True)
        self.cpu_progress.setFormat("%v%")

        mem_label = QLabel("Память:")
        self.mem_progress = QProgressBar()
        self.mem_progress.setMaximum(100)
        self.mem_progress.setTextVisible(True)
        self.mem_progress.setFormat("%v%")

        layout.addWidget(cpu_label)
        layout.addWidget(self.cpu_progress)
        layout.addSpacing(20)
        layout.addWidget(mem_label)
        layout.addWidget(self.mem_progress)
        logger.debug("UI SystemPanel настроена.")


    def update_stats(self, cpu, memory):
        # logger.debug(f"Обновление статистики SystemPanel: ЦП={cpu:.1f}%, Память={memory:.1f}%.")
        self.cpu_progress.setValue(int(cpu))
        self.mem_progress.setValue(int(memory))