# frontend/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QLineEdit, QPushButton, QLabel, QHBoxLayout
)
from backend.logica import Calculadora


class MainWindow(QMainWindow):
    """Ventana principal que conecta la interfaz con la lógica del backend."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculadora PySide6")
        self.setFixedSize(300, 200)

        self.calc = Calculadora()

        self.input1 = QLineEdit()
        self.input1.setPlaceholderText("Número 1")

        self.input2 = QLineEdit()
        self.input2.setPlaceholderText("Número 2")

        self.resultado = QLabel("Resultado: ")
        self.resultado.setStyleSheet("font-weight: bold;")

        self.boton_sumar = QPushButton("Sumar")
        self.boton_restar = QPushButton("Restar")
        self.boton_multiplicar = QPushButton("Multiplicar")
        self.boton_dividir = QPushButton("Dividir")

        self.boton_sumar.clicked.connect(lambda: self.operar("sumar"))
        self.boton_restar.clicked.connect(lambda: self.operar("restar"))
        self.boton_multiplicar.clicked.connect(lambda: self.operar("multiplicar"))
        self.boton_dividir.clicked.connect(lambda: self.operar("dividir"))

        layout_botones = QHBoxLayout()
        layout_botones.addWidget(self.boton_sumar)
        layout_botones.addWidget(self.boton_restar)
        layout_botones.addWidget(self.boton_multiplicar)
        layout_botones.addWidget(self.boton_dividir)

        layout_principal = QVBoxLayout()
        layout_principal.addWidget(self.input1)
        layout_principal.addWidget(self.input2)
        layout_principal.addLayout(layout_botones)
        layout_principal.addWidget(self.resultado)

        contenedor = QWidget()
        contenedor.setLayout(layout_principal)
        self.setCentralWidget(contenedor)

    def operar(self, operacion: str):
        try:
            a = float(self.input1.text())
            b = float(self.input2.text())
            metodo = getattr(self.calc, operacion)
            r = metodo(a, b)
            self.resultado.setText(f"Resultado: {r}")
        except ValueError as e:
            self.resultado.setText(f"Error: {e}")
