import psycopg2
import xml.etree.ElementTree as ET
from io import StringIO
from backend.almacen.database import conectar

def limpiar_texto(texto):
    if texto:
        return texto.strip() 
    return texto

def convertir_coordenadas(coordenadas_str):
    pass

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

def procesar_datos_cat():
    pass



    


