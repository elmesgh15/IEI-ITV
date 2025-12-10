from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QTextEdit, QFrame, QSpacerItem, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt
from frontend.api_client import APIClient


class VentanaCarga(QWidget):
    def __init__(self):
        super().__init__()

        # Inicializar cliente API
        self.api_client = APIClient()
        self.api_client.carga_completada.connect(self.mostrar_resultado_carga)
        self.api_client.error_ocurrido.connect(self.mostrar_error)

        # Main Layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Set modern dark gradient background
        self.setStyleSheet("""
            VentanaCarga { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
            }
        """)

        # Title
        title = QLabel("Carga del almacén de datos")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px; 
            color: #e8f0f2; 
            font-family: 'Segoe UI', sans-serif; 
            font-weight: bold;
            padding: 10px;
        """)
        main_layout.addWidget(title)

        # Center Content Wrapper
        center_wrapper = QHBoxLayout()
        main_layout.addLayout(center_wrapper)
        
        # Spacer Left
        center_wrapper.addStretch()

        # Center Column
        center_column = QVBoxLayout()
        center_column.setSpacing(20)
        center_wrapper.addLayout(center_column)

        # Source Selection
        source_layout = QHBoxLayout()
        source_layout.setAlignment(Qt.AlignCenter)
        
        source_label = QLabel("Seleccione fuente:")
        source_label.setStyleSheet("""
            font-size: 16px; 
            color: #a8dadc; 
            font-weight: bold;
            background: transparent;
        """)
        source_layout.addWidget(source_label)

        checks_layout = QVBoxLayout()
        checks_layout.setSpacing(8)
        
        check_style = """
            QCheckBox { 
                font-size: 14px; 
                color: #e8f0f2;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #457b9d;
                border-radius: 4px;
                background-color: #1d3557;
            }
            QCheckBox::indicator:checked {
                background-color: #06a77d;
                border-color: #06a77d;
                image: none;
            }
            QCheckBox::indicator:hover {
                border-color: #48cae4;
            }
        """
        
        self.check_todas = QCheckBox("Seleccionar todas")
        self.check_todas.setStyleSheet(check_style)
        
        self.check_galicia = QCheckBox("Galicia")
        self.check_galicia.setStyleSheet(check_style)
        
        self.check_valencia = QCheckBox("Comunitat Valenciana")
        self.check_valencia.setStyleSheet(check_style)
        self.check_valencia.setChecked(True) # Match screenshot example
        
        self.check_catalunya = QCheckBox("Catalunya")
        self.check_catalunya.setStyleSheet(check_style)

        checks_layout.addWidget(self.check_todas)
        checks_layout.addWidget(self.check_galicia)
        checks_layout.addWidget(self.check_valencia)
        checks_layout.addWidget(self.check_catalunya)
        
        source_layout.addSpacing(20)
        source_layout.addLayout(checks_layout)
        center_column.addLayout(source_layout)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)
        buttons_layout.setSpacing(15)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cargar = QPushButton("Cargar")
        self.btn_borrar = QPushButton("Borrar almacén de datos")

        # Styles
        # Cancelar: Transparent with border
        self.btn_cancelar.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #48cae4;
                border: 2px solid #48cae4;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(72, 202, 228, 0.2);
                color: #f1faee;
                border-color: #f1faee;
            }
        """)

        # Cargar: Green gradient
        self.btn_cargar.setCursor(Qt.PointingHandCursor)
        self.btn_cargar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06a77d, stop:1 #048a66);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #05c792, stop:1 #06a77d);
            }
        """)

        # Borrar: Red
        self.btn_borrar.setCursor(Qt.PointingHandCursor)
        self.btn_borrar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e63946, stop:1 #d62828);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f07167, stop:1 #e63946);
            }
        """)

        buttons_layout.addWidget(self.btn_cancelar)
        buttons_layout.addWidget(self.btn_cargar)
        buttons_layout.addWidget(self.btn_borrar)

        center_column.addLayout(buttons_layout)

        # Spacer Right
        center_wrapper.addStretch()

        # Results
        results_label = QLabel("Resultados de la carga:")
        results_label.setStyleSheet("""
            font-size: 18px; 
            color: #a8dadc; 
            margin-top: 20px;
            font-weight: bold;
        """)
        main_layout.addWidget(results_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                border: 2px solid #457b9d;
                border-radius: 8px;
                background-color: #1d3557;
                color: #e8f0f2;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 13px;
                padding: 10px;
                selection-background-color: #457b9d;
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
        self.log_output.setPlaceholderText(
            "Número de registros cargados correctamente: NN\n\n"
            "Registros con errores y reparados:\n"
            "{Fuente de datos, nombre, Localidad, motivo del error, operación realizada}\n\n"
            "Registros con errores y rechazados:\n"
            "{Fuente de datos, nombre, Localidad, motivo del error}"
        )
        main_layout.addWidget(self.log_output)

        # Conectar señales de botones
        self.btn_cargar.clicked.connect(self.ejecutar_carga)
        self.btn_borrar.clicked.connect(self.borrar_almacen)
        self.btn_cancelar.clicked.connect(self.cancelar_operacion)
        
        # Conectar checkbox "Seleccionar todas"
        self.check_todas.stateChanged.connect(self.toggle_todas)
    
    def toggle_todas(self, state):
        """Selecciona o deselecciona todos los checkboxes"""
        checked = (state == Qt.CheckState.Checked.value)
        self.check_galicia.setChecked(checked)
        self.check_valencia.setChecked(checked)
        self.check_catalunya.setChecked(checked)
    
    def ejecutar_carga(self):
        """Ejecuta la carga de datos según las fuentes seleccionadas"""
        galicia = self.check_galicia.isChecked()
        valencia = self.check_valencia.isChecked()
        catalunya = self.check_catalunya.isChecked()
        
        if not (galicia or valencia or catalunya):
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar al menos una fuente de datos.")
            return
        
        # Limpiar log
        self.log_output.clear()
        self.log_output.append("Iniciando carga de datos...\n")
        
        # Deshabilitar botones durante la carga
        self.btn_cargar.setEnabled(False)
        self.btn_borrar.setEnabled(False)
        
        # Ejecutar carga
        self.api_client.cargar_datos(galicia=galicia, valencia=valencia, catalunya=catalunya)
    
    def borrar_almacen(self):
        """Borra todos los datos del almacén"""
        respuesta = QMessageBox.question(
            self, 
            "Confirmar borrado", 
            "¿Está seguro de que desea borrar todos los datos del almacén?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            self.log_output.clear()
            self.log_output.append("Borrando almacén de datos...\n")
            
            # Deshabilitar botones
            self.btn_cargar.setEnabled(False)
            self.btn_borrar.setEnabled(False)
            
            self.api_client.borrar_almacen()
    
    def cancelar_operacion(self):
        """Limpia el log y resetea el formulario"""
        self.log_output.clear()
        self.check_todas.setChecked(False)
        self.check_galicia.setChecked(False)
        self.check_valencia.setChecked(False)
        self.check_catalunya.setChecked(False)
    
    def mostrar_resultado_carga(self, resultado):
        """Muestra el resultado de la carga o borrado en el log"""
        # Rehabilitar botones
        self.btn_cargar.setEnabled(True)
        self.btn_borrar.setEnabled(True)
        
        if resultado.get('success'):
            self.log_output.append("\n=== OPERACIÓN COMPLETADA ===\n")
            self.log_output.append(resultado.get('mensaje', 'Operación exitosa'))
            
            if 'insertados' in resultado:
                self.log_output.append(f"\nTotal insertados: {resultado['insertados']}")
                self.log_output.append(f"Total descartados: {resultado['descartados']}")
            
            if 'detalles' in resultado and resultado['detalles']:
                self.log_output.append("\n=== DETALLES POR FUENTE ===\n")
                for fuente, detalle in resultado['detalles'].items():
                    self.log_output.append(f"\n{fuente.upper()}:")
                    if 'error' in detalle:
                        self.log_output.append(f"  Error: {detalle['error']}")
                    else:
                        self.log_output.append(f"  Insertados: {detalle.get('insertados', 0)}")
                        self.log_output.append(f"  Descartados: {detalle.get('descartados', 0)}")
                        if 'log' in detalle:
                            self.log_output.append(f"\n{detalle['log']}")
            
            QMessageBox.information(self, "Éxito", "Operación completada correctamente.")
        else:
            self.log_output.append("\n=== ERROR ===\n")
            self.log_output.append(resultado.get('mensaje', 'Error desconocido'))
            QMessageBox.warning(self, "Error", resultado.get('mensaje', 'Error en la operación'))
    
    def mostrar_error(self, mensaje):
        """Muestra un mensaje de error"""
        # Rehabilitar botones
        self.btn_cargar.setEnabled(True)
        self.btn_borrar.setEnabled(True)
        
        self.log_output.append(f"\n=== ERROR ===\n{mensaje}\n")
        QMessageBox.critical(self, "Error", f"Error en la operación:\n{mensaje}")

