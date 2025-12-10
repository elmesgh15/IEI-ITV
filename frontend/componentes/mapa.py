from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget

class MapaWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.browser = QWebEngineView()
        self.layout.addWidget(self.browser)

        # Basic HTML with Leaflet
        # Centered on Spain (40.4637, -3.7492)
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

                // Example marker (can be removed or made dynamic later)
                // L.marker([40.4168, -3.7038]).addTo(map)
                //    .bindPopup('Madrid')
                //    .openPopup();
            </script>
        </body>
        </html>
        """
        self.browser.setHtml(html_content)

    def actualizar_marcadores(self, estaciones):
        """
        Actualiza los marcadores en el mapa con la lista de estaciones.
        estaciones: lista de diccionarios con los datos de las estaciones
        """
        if not estaciones:
            # Limpiar marcadores
            js_code = """
                if (window.markersLayer) {
                    window.markersLayer.clearLayers();
                }
            """
            self.browser.page().runJavaScript(js_code)
            return
        
        # Crear código JavaScript para agregar marcadores
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
        
        # Código JavaScript completo
        js_code = f"""
            // Limpiar marcadores anteriores
            if (window.markersLayer) {{
                window.markersLayer.clearLayers();
            }} else {{
                window.markersLayer = L.layerGroup().addTo(map);
            }}
            
            // Agregar nuevos marcadores
            {chr(10).join(js_marcadores)}
            
            // Ajustar vista del mapa a los marcadores
            if (window.markersLayer.getLayers().length > 0) {{
                var group = new L.featureGroup(window.markersLayer.getLayers());
                map.fitBounds(group.getBounds().pad(0.1));
            }}
        """
        
        self.browser.page().runJavaScript(js_code)
