import sys
from PySide6.QtWidgets import QApplication
from graphics.main_window import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    mainWindow = MainWindow()

    mainWindow.show()
    sys.exit(app.exec())