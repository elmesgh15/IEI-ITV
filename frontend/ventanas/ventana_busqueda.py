from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QGridLayout, QSpacerItem, QSizePolicy, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt
from frontend.componentes.mapa import MapaWidget
from frontend.api_client import APIClient


class VentanaBusqueda(QWidget):
    def __init__(self):
        super().__init__()

        # Inicializar cliente API
        self.api_client = APIClient()
        self.api_client.busqueda_completada.connect(self.mostrar_resultados)
        self.api_client.error_ocurrido.connect(self.mostrar_error)

        # Main Scroll Area
        scroll_layout = QVBoxLayout(self)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Evitar scroll horizontal si es posible
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1a1a2e;
                width: 14px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #457b9d, stop:1 #2a4858);
                min-height: 20px;
                border-radius: 7px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Content Widget that holds everything
        self.content_widget = QWidget()
        # Set modern dark gradient for the content widget
        self.content_widget.setStyleSheet("""
            QWidget { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
            }
        """)

        # The Layout we used to have on 'self' is now on 'content_widget'
        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(80, 40, 80, 40)
        main_layout.setSpacing(20)

        self.scroll_area.setWidget(self.content_widget)
        scroll_layout.addWidget(self.scroll_area)
        
        # Title
        title = QLabel("Buscador de Estaciones ITV")
        title.setStyleSheet("""
            font-size: 28px; 
            color: #e8f0f2; 
            font-family: 'Segoe UI', sans-serif; 
            font-weight: bold;
            padding: 10px;
            background: transparent;
        """)
        main_layout.addWidget(title)

        # Top Section: Form (Left) and Map (Right)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(40)
        main_layout.addLayout(top_layout)

        # --- Left: Search Form ---
        form_container = QWidget()
        form_container.setStyleSheet("""
            QWidget {
                background-color: rgba(22, 33, 62, 0.6);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        form_layout = QGridLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(10)
        
        # Labels Style
        label_style = """
            font-size: 14px; 
            color: #a8dadc; 
            font-weight: 600;
            background: transparent;
        """
        
        # Inputs Style
        input_style = """
            QLineEdit, QComboBox {
                border: 2px solid #457b9d;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                background-color: #1d3557;
                color: #f1faee;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #48cae4;
                background-color: #264653;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #457b9d;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #f1faee;
            }
        """
        form_container.setStyleSheet(input_style)

        # Localidad
        lbl_localidad = QLabel("Localidad:")
        lbl_localidad.setStyleSheet(label_style)
        lbl_localidad.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.addWidget(lbl_localidad, 0, 0)
        
        self.input_localidad = QLineEdit()
        form_layout.addWidget(self.input_localidad, 0, 1)

        # Cód. Postal
        lbl_cp = QLabel("Cód. Postal:")
        lbl_cp.setStyleSheet(label_style)
        lbl_cp.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.addWidget(lbl_cp, 1, 0)
        
        self.input_cp = QLineEdit()
        self.input_cp.setFixedWidth(100) # Smaller width for CP
        form_layout.addWidget(self.input_cp, 1, 1)

        # Provincia
        lbl_provincia = QLabel("Provincia:")
        lbl_provincia.setStyleSheet(label_style)
        lbl_provincia.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.addWidget(lbl_provincia, 2, 0)
        
        self.input_provincia = QLineEdit()
        form_layout.addWidget(self.input_provincia, 2, 1)

        # Tipo
        lbl_tipo = QLabel("Tipo:")
        lbl_tipo.setStyleSheet(label_style)
        lbl_tipo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.addWidget(lbl_tipo, 3, 0)
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["", "Estación_fija", "Estación_móvil"])
        form_layout.addWidget(self.combo_tipo, 3, 1)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_buscar = QPushButton("Buscar")
        
        # Button Styles
        self.btn_cancelar.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e63946;
                border: 2px solid #e63946;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(230, 57, 70, 0.2);
                border-color: #f1faee;
                color: #f1faee;
            }
        """)
        
        self.btn_buscar.setCursor(Qt.PointingHandCursor)
        self.btn_buscar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06a77d, stop:1 #048a66);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #05c792, stop:1 #06a77d);
            }
        """)

        buttons_layout.addStretch() # Push buttons to the right
        buttons_layout.addWidget(self.btn_cancelar)
        buttons_layout.addWidget(self.btn_buscar)
        
        # Add buttons to form layout
        form_layout.addLayout(buttons_layout, 4, 1)
        
        # Add spacer to push form up
        vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        form_layout.addItem(vertical_spacer, 5, 1)

        top_layout.addWidget(form_container, stretch=1)


        # --- Right: Map Widget ---
        self.map_container = QFrame()
        self.map_container.setStyleSheet("""
            QFrame {
                border: 4px solid #457b9d;
                border-radius: 12px;
                background-color: #1d3557;
            }
        """)
        # Layout para el contenedor del mapa
        map_layout = QVBoxLayout(self.map_container)
        map_layout.setContentsMargins(4, 4, 4, 4) # Margen interno para que se vea el borde y un poco de fondo

        self.mapa = MapaWidget()
        self.mapa.setMinimumSize(400, 300)
        
        map_layout.addWidget(self.mapa)
        top_layout.addWidget(self.map_container, stretch=2)

        # Bottom Section: Results
        results_label = QLabel("Resultados de la búsqueda:")
        results_label.setStyleSheet("""
            font-size: 18px; 
            color: #a8dadc; 
            margin-top: 10px;
            font-weight: bold;
        """)
        main_layout.addWidget(results_label)

        self.table_results = QTableWidget()
        self.table_results.setColumnCount(7)
        self.table_results.setHorizontalHeaderLabels([
            "Nombre", "Tipo", "Dirección", "Localidad", 
            "Cód. postal", "Provincia", "Descripción"
        ])
        
        # Configurar cabecera para que ocupe todo el ancho
        header = self.table_results.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.table_results.setMinimumHeight(400) # Ensure table is tall enough
        self.table_results.setStyleSheet("""
            QTableWidget {
                border: 2px solid #457b9d;
                border-radius: 8px;
                gridline-color: #2a4858;
                background-color: #1d3557;
                color: #f1faee;
            }
            QHeaderView {
                background-color: #1d3557;
            }
            QTableCornerButton::section {
                background-color: #1d3557; 
                border: 1px solid #457b9d;
            }
            QTableWidget::item {
                padding: 8px;
                color: #e8f0f2;
            }
            QTableWidget::item:selected {
                background-color: #457b9d;
                color: #ffffff;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #264653, stop:1 #1d3557);
                color: #48cae4;
                padding: 10px;
                border: 1px solid #457b9d;
                font-weight: bold;
                font-size: 13px;
            }
            QScrollBar:vertical {
                background-color: #1d3557;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #457b9d;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #48cae4;
            }
        """)
        main_layout.addWidget(self.table_results)

        # Conectar señales de botones
        self.btn_buscar.clicked.connect(self.realizar_busqueda)
        self.btn_cancelar.clicked.connect(self.limpiar_formulario)
    
    def realizar_busqueda(self):
        """Ejecuta la búsqueda usando los filtros del formulario"""
        localidad = self.input_localidad.text().strip() or None
        codigo_postal = self.input_cp.text().strip() or None
        provincia = self.input_provincia.text().strip() or None
        tipo = self.combo_tipo.currentText().strip() or None
        
        # Si el tipo está vacío (primera opción), enviarlo como None
        if tipo == "":
            tipo = None
        
        # Realizar la búsqueda
        self.api_client.buscar_estaciones(
            localidad=localidad,
            codigo_postal=codigo_postal,
            provincia=provincia,
            tipo=tipo
        )
    
    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
        self.input_localidad.clear()
        self.input_cp.clear()
        self.input_provincia.clear()
        self.combo_tipo.setCurrentIndex(0)
        self.table_results.setRowCount(0)
        self.mapa.actualizar_marcadores([])
    
    def mostrar_resultados(self, estaciones):
        """Muestra los resultados de la búsqueda en la tabla y el mapa"""
        self.table_results.setRowCount(len(estaciones))
        
        for i, estacion in enumerate(estaciones):
            self.table_results.setItem(i, 0, QTableWidgetItem(estacion.get('nombre', '')))
            self.table_results.setItem(i, 1, QTableWidgetItem(estacion.get('tipo', '')))
            self.table_results.setItem(i, 2, QTableWidgetItem(estacion.get('direccion', '')))
            self.table_results.setItem(i, 3, QTableWidgetItem(estacion.get('localidad', '')))
            self.table_results.setItem(i, 4, QTableWidgetItem(estacion.get('codigo_postal', '')))
            self.table_results.setItem(i, 5, QTableWidgetItem(estacion.get('provincia', '')))
            self.table_results.setItem(i, 6, QTableWidgetItem(estacion.get('descripcion', '')))
        
        # Actualizar mapa con marcadores
        self.mapa.actualizar_marcadores(estaciones)
        
        # Mostrar mensaje si no hay resultados
        if len(estaciones) == 0:
            QMessageBox.information(self, "Búsqueda", "No se encontraron estaciones con los criterios especificados.")
    
    def mostrar_error(self, mensaje):
        """Muestra un mensaje de error"""
        QMessageBox.critical(self, "Error", f"Error en la operación:\n{mensaje}")

