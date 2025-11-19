import json
import psycopg2
import requests
import time
import os
import sys

# Ajuste para permitir la importación de módulos hermanos si se ejecuta como script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.almacen.database import conectar

def limpiar_texto(texto):
    """Limpia espacios y normaliza el texto."""
    if isinstance(texto, str):
        return texto.strip()
    return texto

def obtener_coordenadas(direccion, municipio, provincia):
    """
    Obtiene latitud y longitud consultando la URL solicitada: coordenadas-gps.com.
    """
    # Construimos la dirección de búsqueda
    busqueda = f"{direccion}, {municipio}, {provincia}, España"
    
    url = "https://www.coordenadas-gps.com" 
    
    params = {
        'q': busqueda,
        'format': 'json'
    }
    
    headers = {
        'User-Agent': 'ProyectoIntegracionITV/1.0' 
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                lat = None
                lon = None
                
                if isinstance(data, list) and len(data) > 0:
                    item = data[0]
                    lat = float(item.get('lat', item.get('latitude', 0)))
                    lon = float(item.get('lon', item.get('longitude', 0)))
                elif isinstance(data, dict):
                    lat = float(data.get('lat', data.get('latitude', 0)))
                    lon = float(data.get('lon', data.get('longitude', 0)))
                    
                if lat and lon:
                    return lat, lon
            except json.JSONDecodeError:
                pass
        
        time.sleep(1) 
        
    except Exception as e:
        print(f"Error al geocodificar '{busqueda}': {e}")
    
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
        cursor.execute("INSERT INTO Localidad (nombre, codigo_provincia) VALUES (%s, %s) RETURNING codigo", (nombre_localidad, provincia_id))
        return cursor.fetchone()[0]

def leer_datos_cv():
    base_dir = os.path.dirname(os.path.abspath(__file__)) 
    ruta_archivo_json = os.path.join(base_dir, '..', 'datos', 'estaciones.json') 
    
    print(f"Buscando archivo en: {ruta_archivo_json}")
    
    try:
        with open(ruta_archivo_json, mode='r', encoding='utf-8') as f:
            datos = json.load(f)
        return datos
    except FileNotFoundError:
        print(f"ERROR: No se encuentra el archivo en {ruta_archivo_json}.")
        return None
    except Exception as e:
        print(f"Error al leer el archivo JSON: {e}")
        return None
    
def extraer_datos_temporalmente():
    ruta_archivo_json = "datos/estaciones.json"
    try:
        with open(ruta_archivo_json, mode='r', encoding='latin-1') as f:
            datos_json_texto = f.read()
        return datos_json_texto
    except Exception as e:
        print(f"Error al leer el archivo json: {e}")
        return None

def normalizar_tipo_estacion(tipo_origen):
    if not tipo_origen:
        return "Otros"
    
    tipo = str(tipo_origen).lower()
    if "fija" in tipo:
        return "Estación_fija"
    elif "móvil" in tipo or "movil" in tipo:
        return "Estación_móvil"
    else:
        return "Otros"

def procesar_datos_cv():
    datos_json = extraer_datos_temporalmente()
    
    # Inicializamos contadores
    registros_insertados = 0
    registros_omitidos = 0
    
    if not datos_json:
        print("No se pudieron cargar los datos.")
        return 0, 0

    conn = None
    cur = None
    
    try:
        conn = conectar()
        cur = conn.cursor()
        
        total_registros = len(datos_json)
        print(f"Iniciando procesamiento de {total_registros} registros CV...")

        for item in datos_json:
            # --- Validación de Datos ---
            provincia_nombre = limpiar_texto(item.get('PROVINCIA'))
            localidad_nombre = limpiar_texto(item.get('MUNICIPIO'))
            
            # Si faltan datos críticos, omitimos el registro y aumentamos el contador de fallos
            if not provincia_nombre or not localidad_nombre:
                # print(f"Registro omitido (faltan datos): Estación {item.get('Nº ESTACIÓN')}")
                registros_omitidos += 1
                continue

            # --- Procesamiento e Inserción ---
            try:
                provincia_id = get_or_create_provincia(cur, provincia_nombre)
                localidad_id = get_or_create_localidad(cur, localidad_nombre, provincia_id)

                nombre_estacion = str(item.get('Nº ESTACIÓN', ''))
                tipo_estacion = normalizar_tipo_estacion(item.get('TIPO ESTACIÓN'))
                direccion = limpiar_texto(item.get('DIRECCIÓN'))
                cp_raw = item.get('C.POSTAL')
                codigo_postal = str(cp_raw).zfill(5) if cp_raw and str(cp_raw).strip() else ""
                horario = limpiar_texto(item.get('HORARIOS'))
                contacto = limpiar_texto(item.get('CORREO'))
                url_web = "" 

                latitud, longitud = obtener_coordenadas(direccion, localidad_nombre, provincia_nombre)

                cur.execute("""
                    INSERT INTO Estacion 
                    (nombre, tipo, direccion, codigo_postal, longitud, latitud, horario, contacto, url, codigo_localidad) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (nombre_estacion, tipo_estacion, direccion, codigo_postal, longitud, latitud, horario, contacto, url_web, localidad_id)
                )
                
                # Si llegamos aquí sin error, contamos como éxito
                registros_insertados += 1
                
                # Feedback visual opcional
                # print(f"Insertada: {nombre_estacion} ({localidad_nombre})")

            except Exception as e_row:
                print(f"Error al procesar fila {item.get('Nº ESTACIÓN')}: {e_row}")
                registros_omitidos += 1

        conn.commit()
        
        print("\n--- Resumen de Carga CV ---")
        print(f"Total registros leídos: {total_registros}")
        print(f"Insertados correctamente: {registros_insertados}")
        print(f"No introducidos (omitidos/error): {registros_omitidos}")
        print("---------------------------\n")

        return registros_insertados, registros_omitidos

    except (Exception, psycopg2.Error) as error:
        print(f"Error crítico de base de datos: {error}")
        if conn:
            conn.rollback()
        return 0, len(datos_json) # Si falla el commit global, todo cuenta como no insertado

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("Conexión cerrada.")

if __name__ == "__main__":
    procesar_datos_cv()