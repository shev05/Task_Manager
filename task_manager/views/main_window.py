from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer

from models.process_model import ProcessTableModel
from models.system_monitor import SystemMonitor
from controllers.process_controller import ProcessController
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
        self.process_controller = ProcessController()
        print(f"Created controller: {self.process_controller}")  # Отладочный вывод

        print("dawdwadwa")

        self.init_ui()
        self.init_timer()


    def init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.system_panel = SystemPanel()
        self.process_table = ProcessTableView()
        self.process_table.set_process_controller(self.process_controller)
        self.process_table.setModel(self.source_model)

        layout.addWidget(self.system_panel)
        layout.addWidget(self.process_table)

        self.setCentralWidget(central_widget)

    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_all)
        self.timer.start(2000)

    def update_all(self):
        cpu, mem = self.system_monitor.update_stats()
        self.system_panel.update_stats(cpu, mem)

        gui_procs, bg_procs = ProcessController.get_processes()
        self.source_model.update_data(gui_procs, bg_procs)