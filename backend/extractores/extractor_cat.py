import psycopg2
import xml.etree.ElementTree as ET
from io import StringIO
from backend.almacen.database import conectar

def limpiar_texto(texto):
    if texto:
        return texto.strip() 
    return texto

def get_texto_from_tag(elemento_xml, nombre_tag):
    """
    Busca una etiqueta dentro de un elemento XML y devuelve su texto limpio.
    Retorna None si la etiqueta no existe.
    """
    tag = elemento_xml.find(nombre_tag)
    if tag is not None and tag.text is not None:
        return limpiar_texto(tag.text)
    return None

def convertir_coordenadas(coordenadas_str):
    if not coordenadas_str:
        return None
    try:
        # En el XML de Cataluña vienen sin punto decimal
        return float(coordenadas_str) / 1000000.0
    except (ValueError, TypeError):
        print(f"No se pudo convertir la coordenada: {coordenadas_str}")
        return None

def get_or_create_provincia(cursor, nombre_provincia):
    cursor.execute("SELECT codigo FROM Provincia WHERE nombre = %s", (nombre_provincia,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]
    else:
        cursor.execute("INSERT INTO Provincia (nombre) VALUES (%s) RETURNING codigo", (nombre_provincia,))
        return cursor.fetchone()[0]

def get_or_create_localidad(cursor, nombre_localidad, provincia_id):
    cursor.execute("SELECT codigo FROM Localidad WHERE nombre = %s AND codigo_provincia = %s", (nombre_localidad, provincia_id))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]
    else:
        cursor.execute("INSERT INTO Localidad (nombre, codigo_provincia) VALUES (%s, %s) RETURNING codigo", (nombre_localidad, provincia_id))
        return cursor.fetchone()[0]

def extraer_datos_temporalmente():
    ruta_archivo_xml = "datos/ITV-CAT.xml"
    try:
        with open(ruta_archivo_xml, mode='r', encoding='utf-8') as f:
            datos_xml_texto = f.read()
        return datos_xml_texto
    except Exception as e:
        print(f"Error al leer el archivo XML: {e}")
        return None

def procesar_datos_catalunya():
    print("Iniciando extractor de Cataluña...")
    
    # 1. EXTRAER
    xml_texto = extraer_datos_temporalmente()
    if not xml_texto:
        return

    try:
        # Parseamos el texto XML a un objeto árbol
        xml_root = ET.fromstring(xml_texto)
    except ET.ParseError as e:
        print(f"Error crítico: XML mal formado. {e}")
        return

    conn = conectar()
    if not conn:
        return
    
    cur = conn.cursor()

    try:
        # Encontramos todas las estaciones. 
        # La estructura suele ser <response><row><row ...> o simplemente <row><row>
        # Usamos .//row/row para buscar filas anidadas en cualquier nivel
        lista_estaciones = xml_root.findall(".//row/row")
        
        print(f"Procesando {len(lista_estaciones)} estaciones encontradas en el XML...")
        
        contador = 0
        for estacion_xml in lista_estaciones:
            
            # --- 2. TRANSFORMAR ---
            
            # Mapeo: P.nombre <- serveis_territorials
            nombre_prov = get_texto_from_tag(estacion_xml, 'serveis_territorials')
            
            # Mapeo: L.nombre <- municipi
            nombre_loc = get_texto_from_tag(estacion_xml, 'municipi')

            if not nombre_prov or not nombre_loc:
                continue # Saltamos si faltan datos clave

            # Obtener IDs
            id_prov = get_or_create_provincia(cur, nombre_prov)
            id_loc = get_or_create_localidad(cur, nombre_loc, id_prov)

            # Mapeo: E.nombre <- denominaci (Es más descriptivo que 'estaci')
            nombre_estacion = get_texto_from_tag(estacion_xml, 'denominaci')

            # Mapeo: E.tipo <- Fijo por defecto
            tipo_estacion = "Estación_fija"

            # Mapeo: E.direccion <- adre_a
            direccion = get_texto_from_tag(estacion_xml, 'adre_a')

            # Mapeo: E.codigo_postal <- cp
            cp_raw = get_texto_from_tag(estacion_xml, 'cp')
            codigo_postal = cp_raw.zfill(5) if cp_raw else None

            # Mapeo: E.horario <- horari_de_servei
            horario = get_texto_from_tag(estacion_xml, 'horari_de_servei')

            # Mapeo: E.contacto <- correu_electr_nic
            contacto = get_texto_from_tag(estacion_xml, 'correu_electr_nic')

            # Mapeo: Coordenadas <- lat, long (dividiendo por 1M)
            lat_raw = get_texto_from_tag(estacion_xml, 'lat')
            long_raw = get_texto_from_tag(estacion_xml, 'long')
            
            latitud = convertir_coordenadas(lat_raw)
            longitud = convertir_coordenadas(long_raw)

            # Mapeo: E.url <- atributo 'url' dentro de la etiqueta <web>
            # La etiqueta <web> se busca aparte para sacar su atributo
            tag_web = estacion_xml.find('web')
            url = None
            if tag_web is not None:
                url = tag_web.get('url')

            # --- 3. CARGAR ---
            cur.execute("""
                INSERT INTO Estacion 
                (nombre, tipo, direccion, codigo_postal, longitud, latitud, 
                 horario, contacto, url, codigo_localidad)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                nombre_estacion, tipo_estacion, direccion, codigo_postal, longitud, latitud,
                horario, contacto, url, id_loc
            ))
            
            contador += 1

        conn.commit()
        print(f"Éxito: Se han insertado {contador} estaciones de Cataluña.")

    except Exception as e:
        print(f"Error en el proceso: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    procesar_datos_catalunya()
    



    


