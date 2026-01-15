"""
Ventana principal de la aplicación IEI-ITV.

Este módulo define la ventana principal con sistema de pestañas que integra:
- Pestaña de búsqueda de estaciones
- Pestaña de carga de datos

Utiliza PySide6 (Qt for Python) para la interfaz gráfica con tema oscuro personalizado.
"""

from PySide6.QtWidgets import QMainWindow, QTabWidget
from frontend.ventanas.ventana_busqueda import VentanaBusqueda
from frontend.ventanas.ventana_carga import VentanaCarga

class MainWindow(QMainWindow):
    """
    Ventana principal con pestañas para Buscador y Carga.
    
    Configura la interfaz principal de la aplicación con:
    - Sistema de pestañas (QTabWidget)
    - Tema oscuro con gradientes
    - Integración de ventanas de búsqueda y carga
    
    Attributes:
        tabs (QTabWidget): Widget de pestañas principal
        ventana_busqueda (VentanaBusqueda): Pestaña de búsqueda de estaciones
        ventana_carga (VentanaCarga): Pestaña de carga de datos
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("IEI - ITV")
        self.resize(1000, 700) # Adjusted size for better visibility

        # Apply dark theme to main window
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
            }
        """)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #457b9d;
                border-radius: 8px;
                background-color: transparent;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #264653, stop:1 #1d3557);
                color: #a8dadc;
                border: 2px solid #457b9d;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #06a77d, stop:1 #048a66);
                color: #ffffff;
                border-color: #06a77d;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #457b9d, stop:1 #2a4858);
                color: #48cae4;
            }
        """)
        self.setCentralWidget(self.tabs)

        self.ventana_busqueda = VentanaBusqueda()
        self.ventana_carga = VentanaCarga()

        self.tabs.addTab(self.ventana_busqueda, "Buscador")
        self.tabs.addTab(self.ventana_carga, "Carga")
