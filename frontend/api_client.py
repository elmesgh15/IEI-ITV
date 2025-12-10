from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import json

class APIClient(QObject):
    """Cliente HTTP para comunicarse con la API FastAPI"""
    
    # Señales para manejar respuestas asíncronas
    busqueda_completada = Signal(list)
    carga_completada = Signal(dict)
    error_ocurrido = Signal(str)
    provincias_recibidas = Signal(list)
    estado_recibido = Signal(dict)
    
    def __init__(self, base_url="http://127.0.0.1:8000"):
        super().__init__()
        self.base_url = base_url
        self.manager = QNetworkAccessManager()
    
    def buscar_estaciones(self, localidad=None, codigo_postal=None, provincia=None, tipo=None):
        """Busca estaciones según los criterios especificados"""
        # Construir URL con parámetros
        params = []
        if localidad:
            params.append(f"localidad={localidad}")
        if codigo_postal:
            params.append(f"codigo_postal={codigo_postal}")
        if provincia:
            params.append(f"provincia={provincia}")
        if tipo:
            params.append(f"tipo={tipo}")
        
        url = f"{self.base_url}/api/buscar"
        if params:
            url += "?" + "&".join(params)
        
        request = QNetworkRequest(QUrl(url))
        reply = self.manager.get(request)
        reply.finished.connect(lambda: self._handle_busqueda_response(reply))
    
    def _handle_busqueda_response(self, reply: QNetworkReply):
        """Maneja la respuesta de búsqueda"""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll().data()
            try:
                estaciones = json.loads(data.decode('utf-8'))
                self.busqueda_completada.emit(estaciones)
            except json.JSONDecodeError as e:
                self.error_ocurrido.emit(f"Error al parsear respuesta: {str(e)}")
        else:
            self.error_ocurrido.emit(f"Error en la búsqueda: {reply.errorString()}")
        
        reply.deleteLater()
    
    def obtener_provincias(self):
        """Obtiene la lista de provincias"""
        url = f"{self.base_url}/api/provincias"
        request = QNetworkRequest(QUrl(url))
        reply = self.manager.get(request)
        reply.finished.connect(lambda: self._handle_provincias_response(reply))
    
    def _handle_provincias_response(self, reply: QNetworkReply):
        """Maneja la respuesta de provincias"""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll().data()
            try:
                provincias = json.loads(data.decode('utf-8'))
                self.provincias_recibidas.emit(provincias)
            except json.JSONDecodeError as e:
                self.error_ocurrido.emit(f"Error al parsear provincias: {str(e)}")
        else:
            self.error_ocurrido.emit(f"Error al obtener provincias: {reply.errorString()}")
        
        reply.deleteLater()
    
    def cargar_datos(self, galicia=False, valencia=False, catalunya=False):
        """Ejecuta la carga de datos"""
        url = f"{self.base_url}/api/cargar"
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        
        payload = {
            "galicia": galicia,
            "valencia": valencia,
            "catalunya": catalunya
        }
        
        reply = self.manager.post(request, json.dumps(payload).encode('utf-8'))
        reply.finished.connect(lambda: self._handle_carga_response(reply))
    
    def _handle_carga_response(self, reply: QNetworkReply):
        """Maneja la respuesta de carga"""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll().data()
            try:
                resultado = json.loads(data.decode('utf-8'))
                self.carga_completada.emit(resultado)
            except json.JSONDecodeError as e:
                self.error_ocurrido.emit(f"Error al parsear respuesta de carga: {str(e)}")
        else:
            self.error_ocurrido.emit(f"Error en la carga: {reply.errorString()}")
        
        reply.deleteLater()
    
    def borrar_almacen(self):
        """Borra todos los datos del almacén"""
        url = f"{self.base_url}/api/almacen"
        request = QNetworkRequest(QUrl(url))
        reply = self.manager.deleteResource(request)
        reply.finished.connect(lambda: self._handle_borrar_response(reply))
    
    def _handle_borrar_response(self, reply: QNetworkReply):
        """Maneja la respuesta de borrado"""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll().data()
            try:
                resultado = json.loads(data.decode('utf-8'))
                self.carga_completada.emit(resultado)
            except json.JSONDecodeError as e:
                self.error_ocurrido.emit(f"Error al parsear respuesta: {str(e)}")
        else:
            self.error_ocurrido.emit(f"Error al borrar almacén: {reply.errorString()}")
        
        reply.deleteLater()
    
    def obtener_estado(self):
        """Obtiene el estado del almacén"""
        url = f"{self.base_url}/api/estado"
        request = QNetworkRequest(QUrl(url))
        reply = self.manager.get(request)
        reply.finished.connect(lambda: self._handle_estado_response(reply))
    
    def _handle_estado_response(self, reply: QNetworkReply):
        """Maneja la respuesta de estado"""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll().data()
            try:
                estado = json.loads(data.decode('utf-8'))
                self.estado_recibido.emit(estado)
            except json.JSONDecodeError as e:
                self.error_ocurrido.emit(f"Error al parsear estado: {str(e)}")
        else:
            self.error_ocurrido.emit(f"Error al obtener estado: {reply.errorString()}")
        
        reply.deleteLater()
