import json
import time
import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from backend.almacen.database import conectar
from backend.extractores.filtros import Validate

def limpiar_texto(texto):
    if isinstance(texto, str):
        return texto.strip()
    return texto

def iniciar_driver():
    print("Iniciando navegador Selenium...")
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def obtener_coordenadas(driver, direccion, municipio, provincia):
    busqueda = f"{direccion}, {municipio}, {provincia}, España"
    url = "https://www.coordenadas-gps.com"
    
    try:
        if driver.current_url != url and not driver.current_url.startswith(url):
            driver.get(url)
            try:
                boton_cookies = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceptar') or contains(text(), 'Consent')]"))
                )
                boton_cookies.click()
            except:
                pass 

        input_address = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "address"))
        )
        input_address.clear()
        input_address.send_keys(busqueda)

        boton_buscar = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-primary') and contains(text(), 'GPS')]")
        boton_buscar.click()

        time.sleep(5) 
        
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
    ruta_archivo_json = "backend/datos_nuevos/estaciones.json"
    try:
        with open(ruta_archivo_json, mode='r', encoding='utf-8') as f:
            datos_json = json.load(f)
        return datos_json
    except FileNotFoundError:
        print(f"Error: No se encuentra el archivo en {ruta_archivo_json}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: El archivo no es un JSON válido. {e}")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None

def normalizar_tipo_estacion(tipo_origen):
    if not tipo_origen: return "Otros"
    tipo = str(tipo_origen).lower()
    if "fija" in tipo: return "Estación_fija"
    elif "móvil" in tipo or "movil" in tipo: return "Estación_móvil"
    else: return "Otros"





def procesar_datos_cv():

    print(f"------- Inicio -------")
    print("Iniciando extractor de la Comunidad Valenciana...")

    datos_json = leer_datos_cv()
    
    if not datos_json:
        print("No se pudieron extraer los datos.")
        return
    
    driver = iniciar_driver()

    conn = None
    cur = None
    
    conn = conectar()
    cur = conn.cursor()
    filtro = Validate(cur)

    contadores = {'insertados': 0, 'descartados': 0, 'cp': 0, 'coordenadas': 0, 'nombre': 0, 'provincia': 0, 'datos': 0, 'modificados': 0}

    try:

        total = len(datos_json)

        print(f"Procesando {total} estaciones encontradas en el JSON...")

        print(f"------- Seguimiento de la ejecución -------")

        for i, item in enumerate(datos_json):
            
            nombre_estacion = str(item.get('Nº ESTACIÓN', ''))

            nombre_prov = limpiar_texto(item.get('PROVINCIA'))
            nombre_prov_final = filtro.estandarizar_nombre_provincia(nombre_prov)

            nombre_loc = limpiar_texto(item.get('MUNICIPIO'))
            
            if not nombre_loc and nombre_prov:
                nombre_loc = nombre_prov_final
            
            tipo_estacion = normalizar_tipo_estacion(item.get('TIPO ESTACIÓN'))

            direccion = limpiar_texto(item.get('DIRECCIÓN'))
                
            cp_raw = item.get('C.POSTAL')
            codigo_postal = filtro.validar_y_formatear_cp(cp_raw, comunidad_destino='CV')

            horario = limpiar_texto(item.get('HORARIOS'))

            contacto = limpiar_texto(item.get('CORREO'))

            url_web = "www.sitval.com" 

            print(f"\nInsertando datos [{i+1}/{total}], estacion: {nombre_estacion} ({nombre_loc}, {nombre_prov})")

            print(f"--[{i+1}/{total}] Buscando coords para: {nombre_estacion} ({nombre_loc})...")
            latitud, longitud = obtener_coordenadas(driver, direccion, nombre_loc, nombre_prov)

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
            
            if (tipo_estacion == "Estación_móvil" or tipo_estacion == "Otros") and codigo_postal !="":
                codigo_postal = ""
                contadores['modificados'] += 1
                print(f"--CP modificado, ya que, tipo: {tipo_estacion} no puede contener un CP.")

            if not filtro.tiene_coordenadas_validas(latitud, longitud):
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
                (nombre_estacion, tipo_estacion, direccion, codigo_postal, longitud, latitud, horario, contacto, url_web, localidad_id)
            )
            
            print(f"--Insertado correctamente.")

            contadores['insertados'] += 1

        conn.commit()

        print("\n------- Resumen Final Comunidad Valenciana -------")
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

    except Exception as e:
        print(f"Error en el proceso: {e}")
        if conn: 
            conn.rollback()

    finally:
        if driver: 
            driver.quit()
        if cur: 
            cur.close()
        if conn: 
            conn.close()

if __name__ == "__main__":
    procesar_datos_cv()