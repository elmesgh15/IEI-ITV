import csv
import re
from io import StringIO

from backend.almacen.database import conectar
from backend.extractores.filtros import Validate

def limpiar_texto(texto):
    if texto:
        return texto.strip() 
    return texto

def convertir_coordenadas(coord_str):
    if not coord_str:
        return None
    
    coord_limpia = coord_str.strip()

    try:
        return float(coord_limpia)
    except ValueError:
        pass

    patron = re.compile(r"(-?\d+)[°º\s]+(\d+\.?\d*)")
    match = patron.search(coord_limpia)
    
    if match:
        try:
            grados = float(match.group(1))
            minutos = float(match.group(2))
            
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
    
def leer_datos_gal():
    ruta_archivo_csv = "backend/datos_nuevos/Estacions_ITV.csv"
    try:
        with open(ruta_archivo_csv, mode='r', encoding='utf-8') as f:
            datos_csv_texto = f.read()
        return datos_csv_texto
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
        return None
    




def procesar_datos_gal():

    print(f"------- Inicio -------")
    print(f"Iniciando extractor de Galicia...")

    datos_csv_galicia = leer_datos_gal()
    
    if not datos_csv_galicia:
        print("No se pudieron extraer los datos.")
        return

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
    procesar_datos_gal()