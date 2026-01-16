"""
Extractor de datos de estaciones ITV de Galicia.

Este módulo procesa archivos CSV con información de estaciones ITV de Galicia,
valida los datos, convierte coordenadas del formato DMS a decimal, y los inserta
en la base de datos PostgreSQL.

Archivo fuente: backend/datos_nuevos/Estacions_ITV.csv
Formato: CSV delimitado por punto y coma (;)
Codificación: UTF-8
Campos principales: NOME DA ESTACIÓN, PROVINCIA, CONCELLO, ENDEREZO, CÓDIGO POSTAL,
                    COORDENADAS GMAPS, HORARIO, TELÉFONO, CORREO ELECTRÓNICO

El proceso incluye validaciones exhaustivas de:
- Nombres duplicados
- Provincias válidas
- Códigos postales (formato y prefijo por comunidad)
- Coordenadas GPS (rango geográfico de España)
"""

import csv
import re
import sys
from io import StringIO
from typing import Optional, Tuple

from backend.almacen.database import conectar
from backend.extractores.filtros import Validate

def limpiar_texto(texto: Optional[str]) -> Optional[str]:
    """
    Elimina espacios en blanco al inicio y final de un texto.
    
    Args:
        texto: Cadena de texto a limpiar, puede ser None
    
    Returns:
        Texto limpio sin espacios laterales, o None si la entrada es None
    
    Example:
        >>> limpiar_texto("  Hola Mundo  ")
        'Hola Mundo'
        >>> limpiar_texto(None)
        None
    """
    if texto:
        return texto.strip() 
    return texto

def convertir_coordenadas(coord_str: Optional[str]) -> Optional[float]:
    """
    Convierte coordenadas de formato DMS (grados, minutos) a formato decimal.
    
    Soporta múltiples formatos de entrada:
    - Decimal directo: "42.345678" → 42.345678
    - Grados y minutos: "42° 20.74" → 42.345667
    - Variantes con símbolos: "42º 20.74", "42 20.74"
    
    Args:
        coord_str: Cadena con la coordenada en formato DMS o decimal
    
    Returns:
        Coordenada en formato decimal (float), o None si no se puede convertir
    
    Algorithm:
        Para formato DMS:
        1. Extrae grados y minutos usando regex
        2. Convierte: decimal = grados + (minutos / 60)
        3. Si grados es negativo: decimal = grados - (minutos / 60)
    
    Examples:
        >>> convertir_coordenadas("42.345678")
        42.345678
        >>> convertir_coordenadas("42° 20.74")
        42.345667
        >>> convertir_coordenadas("-8° 30.5")
        -8.508333
        >>> convertir_coordenadas("invalid")
        None
    """
    if not coord_str:
        return None
    
    coord_limpia = coord_str.strip()

    # Intentar conversión directa a decimal
    try:
        return float(coord_limpia)
    except ValueError:
        pass

    # Patrón para formato DMS: grados° minutos
    # Captura: (-?\d+) = grados con signo opcional, (\d+\.?\d*) = minutos con decimales
    patron = re.compile(r"(-?\d+)[°º\s]+(\d+\.?\d*)")
    match = patron.search(coord_limpia)
    
    if match:
        try:
            grados = float(match.group(1))
            minutos = float(match.group(2))
            
            # Aplicar fórmula de conversión respetando el signo
            if grados < 0:
                decimal = grados - (minutos / 60)
            else:
                decimal = grados + (minutos / 60)
                
            return round(decimal, 6)
        except ValueError:
            return None
    
    return None

def get_or_create_provincia(cursor, nombre_provincia: str) -> int:
    """
    Obtiene el código de una provincia o la crea si no existe.
    
    Args:
        cursor: Cursor de base de datos PostgreSQL
        nombre_provincia: Nombre de la provincia
    
    Returns:
        Código (ID) de la provincia
    
    Note:
        Utiliza RETURNING para obtener el ID en una sola query al insertar.
    """
    cursor.execute("SELECT codigo FROM Provincia WHERE nombre = %s", (nombre_provincia,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]
    else:
        cursor.execute("INSERT INTO Provincia (nombre) VALUES (%s) RETURNING codigo", (nombre_provincia,))
        return cursor.fetchone()[0]

def get_or_create_localidad(cursor, nombre_localidad: str, provincia_id: int) -> int:
    """
    Obtiene el código de una localidad o la crea si no existe.
    
    Args:
        cursor: Cursor de base de datos PostgreSQL
        nombre_localidad: Nombre de la localidad/municipio
        provincia_id: Código de la provincia a la que pertenece
    
    Returns:
        Código (ID) de la localidad
    
    Note:
        La búsqueda se hace por nombre Y provincia para evitar duplicados
        entre localidades con el mismo nombre en diferentes provincias.
    """
    cursor.execute("SELECT codigo FROM Localidad WHERE nombre = %s AND codigo_provincia = %s", (nombre_localidad, provincia_id))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]
    else:
        cursor.execute("INSERT INTO Localidad (nombre, codigo_provincia) VALUES (%s, %s) RETURNING codigo", (nombre_localidad, provincia_id))
        return cursor.fetchone()[0]
    
def leer_datos_gal() -> Optional[str]:
    """
    Lee el archivo CSV de estaciones ITV de Galicia.
    
    Returns:
        Contenido completo del archivo CSV como string, o None si hay error
    
    Raises:
        Imprime error en consola pero no lanza excepción
    """
    ruta_archivo_csv = "backend/datos_nuevos/Estacions_ITV.csv"
    try:
        with open(ruta_archivo_csv, mode='r', encoding='utf-8') as f:
            datos_csv_texto = f.read()
        return datos_csv_texto
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
        return None
    




def procesar_datos_gal() -> dict:
    """
    Procesa y carga datos de estaciones ITV de Galicia en la base de datos.
    
    Esta es la función principal del extractor de Galicia. Realiza el proceso completo:
    1. Lee el archivo CSV de estaciones
    2. Parsea los datos con csv.DictReader
    3. Para cada estación:
       - Extrae y limpia los campos
       - Valida provincia, localidad, CP y coordenadas
       - Convierte coordenadas DMS a decimal
       - Descarta registros inválidos con logging detallado
       - Inserta registros válidos en la BD
    4. Hace commit de la transacción
    5. Retorna estadísticas del proceso
    
    Returns:
        dict: Diccionario con:
            - insertados (int): Cantidad de registros insertados exitosamente
            - descartados (int): Cantidad de registros rechazados
            - log (str): Log completo del proceso con detalles de cada operación
    
    Validaciones aplicadas (en orden):
        1. Provincia y localidad no vacías
        2. Nombre de estación no duplicado
        3. Provincia válida (existe en MAPA_PROVINCIAS)
        4. Código postal válido para estaciones fijas
        5. CP vacío para estaciones móviles/otros
        6. Coordenadas dentro del rango geográfico de España
    
    Note:
        - Usa StringIO para capturar logs sin afectar stdout global
        - Todas las operaciones de BD están en una transacción
        - En caso de error, hace rollback automático
        - Los contadores incluyen métricas detalladas por tipo de descarte
    
    Example:
        >>> resultado = procesar_datos_gal()
        >>> print(f"Insertados: {resultado['insertados']}")
        >>> print(f"Descartados: {resultado['descartados']}")
    """

    # Buffer local
    output_buffer = StringIO()

    # Función auxiliar print
    def print(*args, **kwargs):
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', '\n')
        msg = sep.join(map(str, args)) + end
        output_buffer.write(msg)
        sys.__stdout__.write(msg)

    print(f"------- Inicio -------")
    print(f"Iniciando extractor de Galicia...")

    datos_csv_galicia = leer_datos_gal()
    
    if not datos_csv_galicia:
        print("No se pudieron extraer los datos.")
        return {
            'insertados': 0,
            'descartados': 0,
            'log': output_buffer.getvalue()
        }

    conn = None
    cur = None

    conn = conectar()
    cur = conn.cursor()
    filtro = Validate(cur)
    
    contadores = {'insertados': 0, 'descartados': 0, 'cp': 0, 'coordenadas': 0, 'nombre': 0, 'provincia': 0, 'datos': 0, 'modificados': 0}

    try:
        
        lista_estaciones = list(csv.DictReader(StringIO(datos_csv_galicia), delimiter=';'))
        total = len(lista_estaciones)
        
        print(f"Procesando {total} estaciones encontradas en el CSV...")

        print(f"------- Seguimiento de la ejecución -------")

        for i, item in enumerate(lista_estaciones):
                
            nombre_estacion = limpiar_texto(item.get('NOME DA ESTACIÓN'))

            nombre_prov = limpiar_texto(item.get('PROVINCIA'))
            nombre_prov_final = filtro.estandarizar_nombre_provincia(nombre_prov)

            nombre_loc = limpiar_texto(item.get('CONCELLO'))

            tipo_estacion = 'Estación_fija'

            direccion = limpiar_texto(item.get('ENDEREZO'))

            cp_raw = item.get('CÓDIGO POSTAL')
            codigo_postal = filtro.validar_y_formatear_cp(cp_raw, comunidad_destino='GAL')
            horario = limpiar_texto(item.get('HORARIO'))

            tel = limpiar_texto(item.get('TELÉFONO'))
            email = limpiar_texto(item.get('CORREO ELECTRÓNICO'))

            contacto = f"Tel: {tel} " if tel else ""
            if email:
                if contacto:
                    contacto += f"| Email: {email}"
                else:
                    contacto = f"Email: {email}"
                
            url = limpiar_texto(item.get('SOLICITUDE DE CITA PREVIA'))

            coordenadas_str = item.get('COORDENADAS GMAPS')
                
            if coordenadas_str and ',' in coordenadas_str:
                partes = coordenadas_str.split(',')
                if len(partes) == 2:
                    latitud = convertir_coordenadas(partes[0])
                    longitud = convertir_coordenadas(partes[1])

            print(f"\nInsertando datos [{i+1}/{total}], estacion: {nombre_estacion} ({nombre_loc}, {nombre_prov})")

            if not nombre_prov or not nombre_loc:
                print(f"--Descartado (Falta provincia/localiad).")
                contadores['descartados'] +=1
                contadores['datos'] += 1
                continue 

            if not nombre_estacion or filtro.es_duplicado(nombre_estacion):
                print(f"--Descartado (Nombre duplicado), nombre duplicado: {nombre_estacion}.")
                contadores['descartados'] += 1
                contadores['nombre'] += 1
                continue

            if not filtro.es_provincia_real(nombre_prov_final):
                print(f"--Descartado (Provincia no válida), nombre provincia: {nombre_prov}.")
                contadores['descartados'] += 1
                contadores['provincia'] += 1
                continue

            if tipo_estacion == "Estación_fija" and codigo_postal == "":
                print(f"--Descartado (CP inválido), cp: {cp_raw}.")
                contadores['descartados'] += 1
                contadores['cp'] += 1
                continue
            
            if tipo_estacion == "Estación_móvil" or tipo_estacion == "Otros":
                codigo_postal = ""
                contadores['modificados'] += 1
                print(f"--CP modificado, ya que, tipo: {tipo_estacion} no puede contener un CP.")

            if not filtro.tiene_coordenadas_validas(latitud, longitud, 'GAL'):
                print(f"--Descartado (Sin coordenadas válidas), coordenadas: ({latitud},{longitud}).")
                contadores['descartados'] += 1
                contadores['coordenadas'] += 1
                continue

                
            provincia_id = get_or_create_provincia(cur, nombre_prov_final)
            localidad_id = get_or_create_localidad(cur, nombre_loc, provincia_id)
            
            cur.execute("""
                INSERT INTO Estacion 
                (nombre, tipo, direccion, codigo_postal, longitud, latitud, horario, contacto, url, codigo_localidad) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (nombre_estacion, tipo_estacion, direccion, codigo_postal, longitud, latitud, horario, contacto, url, localidad_id)
            )
                
            print(f"--Insertado correctamente.")

            contadores['insertados'] += 1

        conn.commit()
        
        print("\n------- Resumen Final Galicia -------")
        print(f"Se han insertado : {contadores['insertados']} correctamente en la base de datos.")
        print(f"Se han descartado : {contadores['descartados']}.")
        print(f"------- Resumen de los campos ({contadores['descartados']}) descartados. -------")
        print(f"Se han descartado : {contadores['cp']} por tener el CP mal registrado.")
        print(f"Se han descartado : {contadores['datos']} por falta de datos en la provincia o localiad.")
        print(f"Se han descartado : {contadores['coordenadas']} por tener las coordenadas mal registradas.")
        print(f"Se han descartado : {contadores['nombre']} por tener el nombre de la estación duplicado.")
        print(f"Se han descartado : {contadores['provincia']} por tener una provincia que no existe.")
        print(f"------- Resumen de los campos ({contadores['modificados']}) modificados. -------")
        print(f"Se han modificado: {contadores['modificados']} por tener un CP en tipos de estación incorrectos.")
        print(f"------- Final -------")
        
        return {
            'insertados': contadores['insertados'],
            'descartados': contadores['descartados'],
            'log': output_buffer.getvalue()
        }

    except Exception as e:
        print(f"Error en el proceso: {e}")
        if conn:
            conn.rollback()
        return {
            'insertados': contadores.get('insertados', 0),
            'descartados': contadores.get('descartados', 0),
            'log': output_buffer.getvalue()
        }

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    result = procesar_datos_gal()
    print(result)