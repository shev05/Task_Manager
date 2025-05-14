import sys
from PyQt5.QtWidgets import QApplication
# Импортируем наш логгер
from utils.loggerService.logger import logger

from views.main_window import TaskManagerWindow


def main():
    # Логгируем старт приложения
    logger.info("Приложение Task Manager запускается.")

    app = QApplication(sys.argv)
    window = TaskManagerWindow()
    window.show()
    exit_code = app.exec_()

    # Логгируем завершение приложения
    logger.info(f"Приложение Task Manager завершено с кодом: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()