# main.py
import sys
from PySide6.QtWidgets import QApplication
from frontend.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec())
