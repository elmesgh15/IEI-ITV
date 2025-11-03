import psycopg2
import csv
from io import StringIO
from backend.almacen.database import conectar


def limpiar_texto(texto):
    if texto:
        return texto.strip() 
    return texto

def convertir_coordenadas(coordenadas_str):
    if not coordenadas_str:
        return None
    try:
        coord_limpia = coordenadas_str.replace("'", "").strip()

        partes = coord_limpia.split('°')
        if len(partes) != 2:
            return None
        
        grados = float(partes[0].strip())
        minutos = float(partes[1])

        if grados < 0:
            grados_decimal = grados - (minutos / 60)
        else:
            grados_decimal = grados + (minutos / 60)
        return round(grados_decimal, 6)
    
    except (ValueError, TypeError, IndexError):
        return None, None

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
        cursor.execute("INSERT INTO Localidad (nombre, codigo_provincia) VALUES (%s, %s) RETURNING id", (nombre_localidad, provincia_id))
        return cursor.fetchone()[0]
    
def extraer_datos_temporalmente():
    ruta_archivo_csv = "datos/Estaciones_ITV.csv"
    try:
        with open(ruta_archivo_csv, mode='r', encoding='utf-8') as f:
            datos_csv_texto = f.read()
        return datos_csv_texto
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
        return None
    
def procesar_datos_galicia():
    # Extraer datos CSV
    datos_csv_galicia = extraer_datos_temporalmente()
    if not datos_csv_galicia:
        print("No se pudieron extraer los datos.")
        return
    # Establecer conexión a la base de datos
    conn = None
    cur = None
    try:
        conn = conectar()
        cur = conn.cursor()

        # Leer datos CSV
        lector_csv = csv.DictReader(StringIO(datos_csv_galicia), delimiter=';')
        lista_de_filas = list(lector_csv)

        for fila in lista_de_filas:
            nombre_estacion = limpiar_texto(fila.get('NOME DA ESTACIÓN'))
            direccion = limpiar_texto(fila.get('ENDEREZO'))
            código_postal = fila.get('CÓDIGO POSTAL')
            localidad_nombre = limpiar_texto(fila.get('CONCELLO'))
            horario = limpiar_texto(fila.get('HORARIO'))
            contacto_tel, contacto_correo = limpiar_texto(fila.get('TELÉFONO')), limpiar_texto(fila.get('CORREO ELECTRÓNICO'))
            url = fila.get('SOLITITUDE DE CITA PREVIA')
            provincia_nombre = limpiar_texto(fila.get('PROVINCIA'))

            coordenadas_str = fila.get('COORDENADAS GMAPS')
            latitud, longitud = convertir_coordenadas(coordenadas_str)

            provincia_id = get_or_create_provincia(cur, provincia_nombre)
            localidad_id = get_or_create_localidad(cur, localidad_nombre, provincia_id)

            cur.execute("""
                INSERT INTO estaciones_itv 
                (nombre, direccion, codigo_postal, localidad_id, horario, contacto_tel, contacto_correo, url, latitud, longitud) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (nombre_estacion, direccion, código_postal, localidad_id, horario, contacto_tel, contacto_correo, url, latitud, longitud)
            )
        conn.commit()

    except (Exception, psycopg2.Error) as error:
        print(f"Error durante el proceso ETL: {error}")
        # MEJORA: Rollback en caso de error
        if conn:
            conn.rollback()

    finally:
    # MEJORA: Asegurar que la conexión siempre se cierre
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("Conexión a la base de datos cerrada.")
    

if __name__ == "__main__":
    procesar_datos_galicia()

        



    
