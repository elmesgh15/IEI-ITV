import unicodedata

class Validate:

    MAPA_PROVINCIAS = {
        # Comunidad Valenciana
        'valencia': 'Valencia',
        'valència': 'Valencia',
        'alicante': 'Alicante',
        'alacant': 'Alicante',
        'castellon': 'Castellón',
        'castello': 'Castellón',
        
        # Galicia
        'a coruna': 'A Coruña',
        'la coruna': 'A Coruña',
        'coruna': 'A Coruña',
        'lugo': 'Lugo',
        'ourense': 'Ourense',
        'orense': 'Ourense',
        'pontevedra': 'Pontevedra',
        
        # Cataluña
        'barcelona': 'Barcelona',
        'girona': 'Girona',
        'gerona': 'Girona',
        'lleida': 'Lleida',
        'lerida': 'Lleida',
        'tarragona': 'Tarragona',

    }

    PREFIJOS_CP = {
        'GAL': {'15', '27', '32', '36'},       # Coruña, Lugo, Ourense, Pontevedra
        'CV':  {'03', '12', '46'},             # Alicante, Castellón, Valencia
        'CAT': {'08', '17', '25', '43'}        # Barcelona, Girona, Lleida, Tarragona
    }

    def __init__(self, cursor):
        self.cursor = cursor

    def _normalizar_para_clave(self, texto):
        if not texto:
            return ""
        texto = str(texto).lower().strip()
        texto_norm = unicodedata.normalize('NFD', texto)
        return ''.join(c for c in texto_norm if unicodedata.category(c) != 'Mn')
    
    def estandarizar_nombre_provincia(self, nombre_sucio):
        if not nombre_sucio:
            return None
            
        clave = self._normalizar_para_clave(nombre_sucio)
        
        if clave in self.MAPA_PROVINCIAS:
            return self.MAPA_PROVINCIAS[clave]
            
        return nombre_sucio.title()

    def es_duplicado(self, nombre_estacion):
        try:
            query = "SELECT cod_estacion FROM Estacion WHERE nombre = %s LIMIT 1"
            self.cursor.execute(query, (nombre_estacion,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            print(f"Error verificando duplicado: {e}")
            return False

    def validar_y_formatear_cp(self, cp_raw, comunidad_destino=None):
        if not cp_raw:
            return ""
        
        cp_str = str(cp_raw).strip()
        
        
        cp_limpio = None
        if len(cp_str) == 4 and cp_str.isdigit():
            cp_limpio = "0" + cp_str
        elif len(cp_str) == 5 and cp_str.isdigit():
            cp_limpio = cp_str
        
        if not cp_limpio:
            return ""

       
        if comunidad_destino:
            prefijos_validos = self.PREFIJOS_CP.get(comunidad_destino)
            prefijo_actual = cp_limpio[:2] 
            
            if prefijos_validos and prefijo_actual not in prefijos_validos:
                return "" 

        return cp_limpio

    def tiene_coordenadas_validas(self, latitud, longitud):
        if latitud is None or longitud is None:
            return False
            
        try:
            lat = float(latitud)
            lon = float(longitud)
            
            LAT_MIN, LAT_MAX = 36.0, 44.0
            LON_MIN, LON_MAX = -10.0, 3.5
            
            en_rango_lat = LAT_MIN <= lat <= LAT_MAX
            en_rango_lon = LON_MIN <= lon <= LON_MAX
            
            if not (en_rango_lat and en_rango_lon):
                return False
                
            return True
            
        except (ValueError, TypeError):
            return False
        
    def es_provincia_real(self, nombre_provincia):
        if not nombre_provincia: return False
        clave = self._normalizar_para_clave(nombre_provincia)
        return clave in self.MAPA_PROVINCIAS