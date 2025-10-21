import psycopg2
import configparser 
import os

def cargar_configuracion():
    config = configparser.ConfigParser()
    ruta_config = os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini')
    
    if not os.path.exists(ruta_config):
        raise FileNotFoundError(f"No se encontró el archivo de configuración en: {os.path.abspath(ruta_config)}")

    config.read(ruta_config)
    
    if 'postgresql' in config:
        return config['postgresql']
    else:
        raise Exception('No se encontró la sección [postgresql] en el archivo config.ini')

def conectar():
    try:
        db_config = cargar_configuracion()
        print("Conectando a la base de datos...")
        conn = psycopg2.connect(**db_config)
        return conn
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def crear_esquema():
    conn = conectar()
    if not conn:
        return

    CREATE_SCHEMA_SQL = """
    -- Crear tipo ENUM para el campo 'tipo' en la tabla Estacion
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_estacion') THEN
            CREATE TYPE tipo_estacion AS ENUM ('Estación_fija', 'Estación_móvil', 'Otros');
        END IF;
    END$$;

    -- 1. Tabla Provincia (sin dependencias)
    CREATE TABLE IF NOT EXISTS Provincia (
        codigo SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL UNIQUE
    );

    -- 2. Tabla Localidad (depende de Provincia)
    CREATE TABLE IF NOT EXISTS Localidad (
        codigo SERIAL PRIMARY KEY,
        nombre VARCHAR(150) NOT NULL,
        codigo_provincia INTEGER NOT NULL,
        CONSTRAINT fk_provincia
            FOREIGN KEY(codigo_provincia)
            REFERENCES Provincia(codigo)
            ON DELETE CASCADE
    );

    -- 3. Tabla Estacion (depende de Localidad y del tipo ENUM)
    CREATE TABLE IF NOT EXISTS Estacion (
        cod_estacion SERIAL PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL,
        tipo tipo_estacion,
        direccion VARCHAR(255),
        codigo_postal VARCHAR(10),
        longitud DECIMAL(9, 6),
        latitud DECIMAL(9, 6),
        descripcion TEXT,
        horario VARCHAR(255),
        contacto VARCHAR(255),
        url VARCHAR(255),
        codigo_localidad INTEGER NOT NULL,
        CONSTRAINT fk_localidad
            FOREIGN KEY(codigo_localidad)
            REFERENCES Localidad(codigo)
            ON DELETE CASCADE
    );
    """
    try:
        with conn:
            with conn.cursor() as cur:
                print("Creando esquema de la base de datos...")
                cur.execute(CREATE_SCHEMA_SQL)
        print("¡Esquema creado o ya existente!")
    except psycopg2.Error as e:
        print(f"Error al crear el esquema: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    crear_esquema()