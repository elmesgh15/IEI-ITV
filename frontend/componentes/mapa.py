from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtCore import Signal
from frontend.api_client import APIClient

class MapaWidget(QWidget):
    estaciones_cargadas = Signal(list)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.browser = QWebEngineView()
        self.layout.addWidget(self.browser)

        # Estado del mapo
        self.map_ready = False
        self.pending_stations = None
        self.should_load_on_ready = False
        
        # Cliente API propio para el mapa
        self.api_client = APIClient()
        self.api_client.busqueda_completada.connect(self._on_estaciones_recibidas)

        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mapa</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
             integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
             crossorigin=""/>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
             integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
             crossorigin=""></script>
            <style>
                body { margin: 0; padding: 0; }
                #map { width: 100%; height: 100vh; }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map').setView([40.4637, -3.7492], 6);

                L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                }).addTo(map);
            </script>
        </body>
        </html>
        """
        self.browser.loadFinished.connect(self._on_load_finished)
        self.browser.setHtml(html_content)

    def _on_load_finished(self, ok):
        """Se ejecuta cuando el HTML del mapa ha terminado de cargar"""
        if ok:
            self.map_ready = True
            
            # Si se solicitó carga mientras no estaba listo, cargar ahora
            if self.should_load_on_ready:
                self.api_client.obtener_todas_estaciones()
                self.should_load_on_ready = False
            
            # Si había actualizaciones pendientes, aplicarlas ahora
            if self.pending_stations is not None:
                self.actualizar_marcadores(self.pending_stations)
                self.pending_stations = None

    def cargar_estaciones(self):
        """Dispara la carga de estaciones desde la API"""
        if self.map_ready:
            self.api_client.obtener_todas_estaciones()
        else:
            self.should_load_on_ready = True

    def _on_estaciones_recibidas(self, estaciones):
        """Callback interno cuando el API devuelve estaciones"""
        # Actualizamos nuestros marcadores SIN zoom (para que no se mueva el mapa al inicio)
        self.actualizar_marcadores(estaciones, zoom=False)
        # Avisamos al exterior (ventana principal) para que actualice la tabla
        self.estaciones_cargadas.emit(estaciones)

    def actualizar_marcadores(self, estaciones, zoom=True):
        """
        Actualiza los marcadores en el mapa con la lista de estaciones.
        estaciones: lista de diccionarios con los datos de las estaciones
        zoom: si es True (default), ajusta la vista para mostrar todos los marcadores.
              si es False, mantiene la vista actual.
        """
        # Si el mapa no está listo, guardamos para luego
        if not self.map_ready:
            self.pending_stations = estaciones
            return

        if not estaciones:
            js_code = """
                if (window.markersLayer) {
                    window.markersLayer.clearLayers();
                }
            """
            self.browser.page().runJavaScript(js_code)
            return
        
        js_marcadores = []
        for estacion in estaciones:
            lat = estacion.get('latitud')
            lon = estacion.get('longitud')
            
            if lat and lon:
                nombre = estacion.get('nombre', 'Sin nombre').replace("'", "\\'")
                tipo = estacion.get('tipo', '').replace("'", "\\'")
                direccion = estacion.get('direccion', '').replace("'", "\\'")
                localidad = estacion.get('localidad', '').replace("'", "\\'")
                provincia = estacion.get('provincia', '').replace("'", "\\'")
                cp = estacion.get('codigo_postal', '')
                
                popup_html = f"""
                    <b>{nombre}</b><br>
                    <i>{tipo}</i><br>
                    {direccion}<br>
                    {localidad}, {provincia} {cp}
                """.replace('\n', ' ').strip()
                
                js_marcadores.append(
                    f"L.marker([{lat}, {lon}]).addTo(window.markersLayer).bindPopup('{popup_html}');"
                )
        
        js_code = f"""
            // Limpiar marcadores anteriores
            if (window.markersLayer) {{
                window.markersLayer.clearLayers();
            }} else {{
                window.markersLayer = L.layerGroup().addTo(map);
            }}
            
            // Agregar nuevos marcadores
            {chr(10).join(js_marcadores)}
        """

        if zoom:
            js_code += """
            // Ajustar vista del mapa a los marcadores
            if (window.markersLayer.getLayers().length > 0) {
                var group = new L.featureGroup(window.markersLayer.getLayers());
                map.fitBounds(group.getBounds().pad(0.1));
            }
            """
        
        self.browser.page().runJavaScript(js_code)

    def enfocar_estaciones(self, estaciones):
        """
        Centra el mapa en las estaciones indicadas sin modificar los marcadores existentes.
        estaciones: lista de diccionarios con los datos de las estaciones a enfocar.
        """
        if not self.map_ready:
            return

        marcadores_coords = []
        for estacion in estaciones:
            lat = estacion.get('latitud')
            lon = estacion.get('longitud')
            if lat and lon:
                marcadores_coords.append(f"[{lat}, {lon}]")
        
        if not marcadores_coords:
            return
            
        js_code = f"""
            var bounds = L.latLngBounds([{', '.join(marcadores_coords)}]);
            map.fitBounds(bounds.pad(0.1));
        """
        self.browser.page().runJavaScript(js_code)
