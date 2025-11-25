import psycopg2
import csv
import re
from io import StringIO
from backend.almacen.database import conectar


def limpiar_texto(texto):
    if texto:
        return texto.strip() 
    return texto

def convertir_coordenadas(coord_str):
    if not coord_str:
        return None
    
    coord_limpia = coord_str.strip()

    # --- CASO 1: Formato Decimal Directo ---
    try:
        # Si Python puede convertirlo directamente a float, ¡ya hemos terminado!
        return float(coord_limpia)
    except ValueError:
        pass

    # --- CASO 2: Formato Grados + Minutos ---
    patron = re.compile(r"(-?\d+)[°º\s]+(\d+\.?\d*)")
    match = patron.search(coord_limpia)
    
    if match:
        try:
            grados = float(match.group(1))
            minutos = float(match.group(2))
            
            # Fórmula: Grados + (Minutos / 60)
            if grados < 0:
                decimal = grados - (minutos / 60)
            else:
                decimal = grados + (minutos / 60)
                
            return round(decimal, 6)
        except ValueError:
            return None
    
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
    ruta_archivo_csv = "backend/datos_nuevos/Estacions_ITV.csv"
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

            provincia_nombre = limpiar_texto(fila.get('PROVINCIA'))
            localidad_nombre = limpiar_texto(fila.get('CONCELLO'))

            if not provincia_nombre or not localidad_nombre:
                print(f"Fila omitida por falta de datos de provincia o localidad: {fila}")
                continue

            provincia_id = get_or_create_provincia(cur, provincia_nombre)
            localidad_id = get_or_create_localidad(cur, localidad_nombre, provincia_id)

            nombre_estacion = limpiar_texto(fila.get('NOME DA ESTACIÓN'))
            tipo_estacion = 'Estación_fija'  # Dato fijo para todas las estaciones de Galicia
            direccion = limpiar_texto(fila.get('ENDEREZO'))
            codigo_postal = fila.get('CÓDIGO POSTAL')

            coordenadas_str = fila.get('COORDENADAS GMAPS')
            latitud = None
            longitud = None
            
            if coordenadas_str and ',' in coordenadas_str:
                # Dividimos por la coma
                partes = coordenadas_str.split(',')
                if len(partes) == 2:
                    # Usamos la nueva función robusta
                    latitud = convertir_coordenadas(partes[0])
                    longitud = convertir_coordenadas(partes[1])
                    
                    # DEBUG: Si sale None, imprimimos para ver por qué falla
                    if latitud is None or longitud is None:
                        print(f"⚠️ Aviso: Fallo al convertir coords: {coordenadas_str}")
            
            horario = limpiar_texto(fila.get('HORARIO'))

            tel = limpiar_texto(fila.get('TELÉFONO'))
            email = limpiar_texto(fila.get('CORREO ELECTRÓNICO'))
            contacto = f"Tel: {tel} " if tel else ""
            if email:
                if contacto:
                    contacto += f"| Email: {email}"
                else:
                    contacto = f"Email: {email}"
            
            url = limpiar_texto(fila.get('SOLICITUDE DE CITA PREVIA'))
            
            cur.execute("""
                INSERT INTO Estacion 
                (nombre, tipo, direccion, codigo_postal, longitud, latitud, horario, contacto, url, codigo_localidad) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (nombre_estacion, tipo_estacion, direccion, codigo_postal, longitud, latitud, horario, contacto, url, localidad_id)
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

        



    
