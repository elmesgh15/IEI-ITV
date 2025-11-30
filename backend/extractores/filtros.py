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

    def __init__(self, cursor):
        """
        Inicializamos la clase con el cursor de la base de datos
        para poder hacer comprobaciones de duplicados.
        """
        self.cursor = cursor

    def _normalizar_para_clave(self, texto):
        """
        Método interno para limpiar texto antes de comparar con la lista blanca.
        Pasa a minúsculas y quita tildes.
        Ej: "A Coruña" -> "a coruna"
        """
        if not texto:
            return ""
        texto = str(texto).lower().strip()
        texto_norm = unicodedata.normalize('NFD', texto)
        return ''.join(c for c in texto_norm if unicodedata.category(c) != 'Mn')
    
    def estandarizar_nombre_provincia(self, nombre_sucio):
        """
        Recibe un nombre (ej: "València", "Gerona") y devuelve el nombre oficial
        configurado en el mapa (ej: "Valencia", "Girona").
        Si no lo encuentra, devuelve el nombre original capitalizado.
        """
        if not nombre_sucio:
            return None
            
        clave = self._normalizar_para_clave(nombre_sucio)
        
        # Buscamos en el diccionario
        if clave in self.MAPA_PROVINCIAS:
            return self.MAPA_PROVINCIAS[clave]
            
        # Si no está en el mapa, lo devolvemos "Bonito" (Primera letra mayúscula)
        return nombre_sucio.title()

    def validar_ubicacion(self, provincia, localidad):
        """
        Filtro de Integridad: Comprueba que provincia y localidad tengan datos.
        Retorna True si son válidos, False si falta alguno.
        """
        if not provincia or not localidad:
            return False
        # Comprobación extra: que no sean cadenas vacías o solo espacios
        if len(provincia.strip()) == 0 or len(localidad.strip()) == 0:
            return False
        return True

    def es_duplicado(self, nombre_estacion):
        """
        Filtro de Duplicados: Consulta a la BD si ya existe ese nombre.
        Retorna True si YA existe (es duplicado), False si es nueva.
        """
        try:
            query = "SELECT cod_estacion FROM Estacion WHERE nombre = %s LIMIT 1"
            self.cursor.execute(query, (nombre_estacion,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            print(f"Error verificando duplicado: {e}")
            return False

    def validar_y_formatear_cp(self, cp_raw):
        """
        Validación de CP:
        - Rellena con ceros a la izquierda si tiene 4 dígitos.
        - Retorna el CP formateado (str) si es válido (5 dígitos).
        - Retorna None si el CP no es válido.
        """
        if not cp_raw:
            return ""
        
        cp_str = str(cp_raw).strip()
        
        # Caso: 4 dígitos (ej: "3600") -> "03600"
        if len(cp_str) == 4 and cp_str.isdigit():
            return "0" + cp_str
        
        # Caso: 5 dígitos (Correcto)
        if len(cp_str) == 5 and cp_str.isdigit():
            return cp_str
            
        # Cualquier otro caso se considera inválido
        return ""

    def tiene_coordenadas_validas(self, latitud, longitud):
        if latitud is None or longitud is None:
            return False
            
        try:
            lat = float(latitud)
            lon = float(longitud)
            
            # Definición del Bounding Box de la Península Ibérica
            LAT_MIN, LAT_MAX = 36.0, 44.0
            LON_MIN, LON_MAX = -10.0, 3.5
            
            # Comprobación del rango
            en_rango_lat = LAT_MIN <= lat <= LAT_MAX
            en_rango_lon = LON_MIN <= lon <= LON_MAX
            
            if not (en_rango_lat and en_rango_lon):
                # Opcional: Descomentar para depurar coordenadas descartadas
                print(f"Coordenadas no válidas: ({lat}, {lon})")
                return False
                
            return True
            
        except (ValueError, TypeError):
            return False
        
    def existe_provincia_en_bd(self, nombre_provincia):
        if not nombre_provincia:
            return False
        query = "SELECT codigo FROM Provincia WHERE nombre = %s LIMIT 1"
        self.cursor.execute(query, (nombre_provincia,))
        return self.cursor.fetchone() is not None

    def es_provincia_real(self, nombre_provincia):
        if not nombre_provincia: return False
        clave = self._normalizar_para_clave(nombre_provincia)
        return clave in self.MAPA_PROVINCIAS