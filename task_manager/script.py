import sys
import os
from PyQt5.QtWidgets import QApplication

from views.main_window import TaskManagerWindow


def main():

    app = QApplication(sys.argv)
    window = TaskManagerWindow()
    print("wadadwawddawwad")
    window.show()
    print("d")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()