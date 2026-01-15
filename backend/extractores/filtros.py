"""
Sistema de validación y normalización de datos para extractores de ITV.

Este módulo centraliza todas las validaciones de datos para los extractores de las
diferentes comunidades autónomas. Proporciona la clase Validate que implementa:

- Normalización de nombres de provincias (variantes → forma canónica)
- Validación de códigos postales (formato y prefijo por comunidad)
- Validación de coordenadas GPS (rango geográfico de España)
- Detección de duplicados en la base de datos
- Estandarización de nombres para comparaciones

Comunidades soportadas:
- Galicia (GAL): A Coruña, Lugo, Ourense, Pontevedra
- Comunidad Valenciana (CV): Alicante, Castellón, Valencia
- Cataluña (CAT): Barcelona, Girona, Lleida, Tarragona
"""

import unicodedata
from typing import Optional

class Validate:
    """
    Clase de validación y normalización de datos de estaciones ITV.
    
    Proporciona métodos para validar y normalizar datos antes de insertarlos
    en la base de datos, asegurando consistencia y calidad de los datos.
    
    Attributes:
        MAPA_PROVINCIAS (dict): Mapeo de variantes de nombres a forma canónica
        PREFIJOS_CP (dict): Prefijos válidos de códigos postales por comunidad
        cursor: Cursor de base de datos para consultas de validación
    
    Example:
        >>> cursor = conn.cursor()
        >>> filtro = Validate(cursor)
        >>> provincia = filtro.estandarizar_nombre_provincia("VALENCIA")
        >>> print(provincia)  # "Valencia"
        >>> cp = filtro.validar_y_formatear_cp("3001", comunidad_destino="CV")
        >>> print(cp)  # "03001"
    """

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

    RANGOS_COORDENADAS = {
        # Aproximaciones rectangulares para validación básica
        'GAL': {'lat_min': 41.5, 'lat_max': 44.0, 'lon_min': -9.5, 'lon_max': -6.5},
        'CV':  {'lat_min': 37.5, 'lat_max': 41.0, 'lon_min': -2.0, 'lon_max': 1.0},
        'CAT': {'lat_min': 40.0, 'lat_max': 43.0, 'lon_min': 0.0, 'lon_max': 3.5},
        'ESP': {'lat_min': 36.0, 'lat_max': 44.0, 'lon_min': -10.0, 'lon_max': 3.5}
    }

    def __init__(self, cursor):
        self.cursor = cursor

    def _normalizar_para_clave(self, texto: Optional[str]) -> str:
        """
        Normaliza texto para usar como clave en comparaciones.
        
        Convierte a minúsculas, elimina acentos y caracteres diacríticos.
        
        Args:
            texto: Texto a normalizar
        
        Returns:
            Texto normalizado (minúsculas, sin acentos)
        
        Example:
            >>> self._normalizar_para_clave("València")
            'valencia'
            >>> self._normalizar_para_clave("A Coruña")
            'a coruna'
        """
        if not texto:
            return ""
        texto = str(texto).lower().strip()
        texto_norm = unicodedata.normalize('NFD', texto)
        return ''.join(c for c in texto_norm if unicodedata.category(c) != 'Mn')
    
    def estandarizar_nombre_provincia(self, nombre_sucio: Optional[str]) -> Optional[str]:
        """
        Convierte variantes de nombres de provincias a su forma canónica.
        
        Args:
            nombre_sucio: Nombre de provincia en cualquier formato/variante
        
        Returns:
            Nombre estandarizado de la provincia, o None si entrada es None.
            Si no está en el mapa, retorna el nombre con title case.
        
        Example:
            >>> estandarizar_nombre_provincia("VALENCIA")
            'Valencia'
            >>> estandarizar_nombre_provincia("alacant")
            'Alicante'
            >>> estandarizar_nombre_provincia("la coruna")
            'A Coruña'
        """
        if not nombre_sucio:
            return None
            
        clave = self._normalizar_para_clave(nombre_sucio)
        
        if clave in self.MAPA_PROVINCIAS:
            return self.MAPA_PROVINCIAS[clave]
            
        return nombre_sucio.title()

    def es_duplicado(self, nombre_estacion: str) -> bool:
        """
        Verifica si ya existe una estación con el mismo nombre en la BD.
        
        Args:
            nombre_estacion: Nombre de la estación a verificar
        
        Returns:
            True si existe una estación con ese nombre, False en caso contrario
        
        Note:
            Retorna False si hay error en la consulta SQL.
        """
        try:
            query = "SELECT cod_estacion FROM Estacion WHERE nombre = %s LIMIT 1"
            self.cursor.execute(query, (nombre_estacion,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            print(f"Error verificando duplicado: {e}")
            return False

    def validar_y_formatear_cp(self, cp_raw, comunidad_destino: Optional[str] = None) -> str:
        """
        Valida y formatea códigos postales españoles.
        
        Normaliza a 5 dígitos y valida que el prefijo corresponda a la comunidad.
        
        Args:
            cp_raw: Código postal en cualquier formato (puede ser 4 o 5 dígitos)
            comunidad_destino: Código de comunidad ('GAL', 'CV', 'CAT') para validar prefijo
        
        Returns:
            Código postal formateado (5 dígitos), o cadena vacía si es inválido
        
        Validation Rules:
            - Debe tener 4 o 5 dígitos numéricos
            - Se normaliza a 5 dígitos (añade 0 al inicio si tiene 4)
            - Si se especifica comunidad, valida que el prefijo sea correcto
        
        Example:
            >>> validar_y_formatear_cp("3001", "CV")
            '03001'
            >>> validar_y_formatear_cp("46001", "CV")
            '46001'
            >>> validar_y_formatear_cp("28001", "CV")  # Madrid, no Valencia
            ''
        """
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

    def tiene_coordenadas_validas(self, latitud, longitud, comunidad='ESP') -> bool:
        """
        Valida que las coordenadas GPS estén dentro del rango geográfico de la comunidad.
        
        Args:
            latitud: Latitud en formato decimal
            longitud: Longitud en formato decimal
            comunidad: Código de la comunidad ('GAL', 'CV', 'CAT', 'ESP')
        
        Returns:
            True si las coordenadas son válidas y están en el rango, False en caso contrario
        """
        if latitud is None or longitud is None:
            return False
            
        try:
            lat = float(latitud)
            lon = float(longitud)
            
            rango = self.RANGOS_COORDENADAS.get(comunidad, self.RANGOS_COORDENADAS['ESP'])
            
            en_rango_lat = rango['lat_min'] <= lat <= rango['lat_max']
            en_rango_lon = rango['lon_min'] <= lon <= rango['lon_max']
            
            if not (en_rango_lat and en_rango_lon):
                return False
                
            return True
            
        except (ValueError, TypeError):
            return False
        
    def es_provincia_real(self, nombre_provincia: Optional[str]) -> bool:
        """
        Verifica que la provincia esté en el mapa de provincias soportadas.
        
        Args:
            nombre_provincia: Nombre de la provincia a verificar
        
        Returns:
            True si la provincia está soportada, False en caso contrario
        
        Note:
            Solo retorna True para provincias de Galicia, Valencia y Cataluña.
        """
        if not nombre_provincia: return False
        clave = self._normalizar_para_clave(nombre_provincia)
        return clave in self.MAPA_PROVINCIAS