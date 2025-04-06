from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt


class SystemPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cpu_progress = None
        self.mem_progress = None
        self.setup_ui()

    def setup_ui(self):
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

    def update_stats(self, cpu, memory):
        self.cpu_progress.setValue(int(cpu))
        self.mem_progress.setValue(int(memory))