import json
import psycopg2
import time
import os
import sys

# Importaciones de Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Ajuste para permitir la importación de módulos hermanos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.almacen.database import conectar

def limpiar_texto(texto):
    """Limpia espacios y normaliza el texto."""
    if isinstance(texto, str):
        return texto.strip()
    return texto

def iniciar_driver():
    """Configura e inicia el navegador Chrome con Selenium."""
    print("Iniciando navegador Selenium...")
    chrome_options = Options()
    # Comenta la siguiente línea si quieres ver el navegador trabajando (útil para depurar)
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def obtener_coordenadas(driver, direccion, municipio, provincia):
    """
    Usa Selenium para obtener coordenadas desde coordenadas-gps.com
    """
    busqueda = f"{direccion}, {municipio}, {provincia}, España"
    url = "https://www.coordenadas-gps.com"
    
    try:
        # Navegar a la web si no estamos ya allí (para reutilizar sesión)
        if driver.current_url != url and not driver.current_url.startswith(url):
            driver.get(url)
            # Aceptamos cookies si aparecen (ajustar selector según la web)
            try:
                boton_cookies = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceptar') or contains(text(), 'Consent')]"))
                )
                boton_cookies.click()
            except:
                pass # Si no hay banner o falla, seguimos

        # 1. Encontrar el campo de dirección y limpiarlo
        input_address = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "address"))
        )
        input_address.clear()
        input_address.send_keys(busqueda)

        # 2. Encontrar el botón de búsqueda y hacer click
        # En esta web suele ser un botón que dice "Obtener Coordenadas GPS"
        boton_buscar = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-primary') and contains(text(), 'GPS')]")
        boton_buscar.click()

        # 3. Esperar a que los campos de latitud/longitud tengan valor
        # Un truco es esperar un poco o esperar a que el valor cambie si ya había uno.
        # Aquí esperaremos a que el input latitude sea visible y tenga valor.
        time.sleep(1.5) # Pausa para dejar que el JS de la web procese (ajustar según velocidad de red)
        
        lat_input = driver.find_element(By.ID, "latitude")
        lon_input = driver.find_element(By.ID, "longitude")
        
        lat_texto = lat_input.get_attribute("value")
        lon_texto = lon_input.get_attribute("value")

        if lat_texto and lon_texto:
            try:
                return float(lat_texto), float(lon_texto)
            except ValueError:
                return None, None

    except (TimeoutException, NoSuchElementException) as e:
        print(f"Selenium no pudo encontrar coordenadas para: {busqueda}. Error: {e}")
        # Opcional: Recargar página si falla mucho
        # driver.refresh()
    except Exception as e:
        print(f"Error general Selenium: {e}")

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
    """Lee el archivo JSON correctamente."""
    # Ruta dinámica para encontrar el archivo JSON
    ruta_archivo_json = "datos_nuevos/estaciones.json"
    
    if not os.path.exists(ruta_archivo_json):
        base_dir = os.path.dirname(os.path.abspath(__file__)) 
        ruta_archivo_json = os.path.join(base_dir, '..', '..', 'datos_nuevos', 'estaciones.json')

    print(f"Leyendo archivo desde: {os.path.abspath(ruta_archivo_json)}")

    try:
        with open(ruta_archivo_json, mode='r', encoding='utf-8') as f:
            # IMPORTANTE: Usar json.load para obtener una LISTA, no un STRING
            datos = json.load(f)
        return datos
    except FileNotFoundError:
        print(f"ERROR: No se encuentra el archivo 'estaciones.json'.")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON inválido: {e}")
        return None
    except Exception as e:
        print(f"Error al leer archivo: {e}")
        return None

def normalizar_tipo_estacion(tipo_origen):
    if not tipo_origen: return "Otros"
    tipo = str(tipo_origen).lower()
    if "fija" in tipo: return "Estación_fija"
    elif "móvil" in tipo or "movil" in tipo: return "Estación_móvil"
    else: return "Otros"

def procesar_datos_cv():
    print("Iniciando proceso ETL con Selenium...")
    
    # 1. Cargar datos
    datos_json = leer_datos_cv()
    
    if datos_json is None:
        print("Abortando: No hay datos.")
        return 0, 0

    if not isinstance(datos_json, list):
        print(f"Error de formato: Se esperaba una lista, se recibió {type(datos_json)}")
        return 0, 0

    # 2. Iniciar Driver (Una sola vez)
    driver = iniciar_driver()

    registros_insertados = 0
    registros_omitidos = 0
    conn = None
    cur = None
    
    try:
        conn = conectar()
        cur = conn.cursor()
        
        total = len(datos_json)
        print(f"Procesando {total} estaciones...")

        for i, item in enumerate(datos_json):
            # --- Validación ---
            provincia_nombre = limpiar_texto(item.get('PROVINCIA'))
            localidad_nombre = limpiar_texto(item.get('MUNICIPIO'))
            
            if not provincia_nombre or not localidad_nombre:
                registros_omitidos += 1
                continue

            try:
                # --- Procesamiento ---
                provincia_id = get_or_create_provincia(cur, provincia_nombre)
                localidad_id = get_or_create_localidad(cur, localidad_nombre, provincia_id)

                nombre_estacion = str(item.get('Nº ESTACIÓN', ''))
                tipo_estacion = normalizar_tipo_estacion(item.get('TIPO ESTACIÓN'))
                direccion = limpiar_texto(item.get('DIRECCIÓN'))
                
                cp_raw = item.get('C.POSTAL')
                codigo_postal = str(cp_raw).zfill(5) if cp_raw and str(cp_raw).strip() else ""
                
                horario = limpiar_texto(item.get('HORARIOS'))
                contacto = limpiar_texto(item.get('CORREO'))
                url_web = "www.sitval.com" 

                # --- Selenium para Coordenadas ---
                print(f"[{i+1}/{total}] Buscando coords para: {nombre_estacion} ({localidad_nombre})...", end="\r")
                latitud, longitud = obtener_coordenadas(driver, direccion, localidad_nombre, provincia_nombre)

                cur.execute("""
                    INSERT INTO Estacion 
                    (nombre, tipo, direccion, codigo_postal, longitud, latitud, horario, contacto, url, codigo_localidad) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (nombre_estacion, tipo_estacion, direccion, codigo_postal, longitud, latitud, horario, contacto, url_web, localidad_id)
                )
                registros_insertados += 1
                
            except Exception as e_row:
                print(f"\nError en fila {i}: {e_row}")
                registros_omitidos += 1

        conn.commit()
        print(f"\n\n--- Resumen Final ---")
        print(f"Insertados: {registros_insertados}")
        print(f"Fallidos/Omitidos: {registros_omitidos}")

        return registros_insertados, registros_omitidos

    except Exception as error:
        print(f"Error crítico: {error}")
        if conn: conn.rollback()
        return 0, 0

    finally:
        # Cerrar navegador y base de datos
        if driver: driver.quit()
        if cur: cur.close()
        if conn: conn.close()
        print("Recursos liberados.")

if __name__ == "__main__":
    procesar_datos_cv()