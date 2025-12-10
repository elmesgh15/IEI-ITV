"""
Script de inicialización del proyecto ITV.
Verifica la configuración y crea el esquema de la base de datos.
"""
import os
import sys

def verificar_config():
    """Verifica que exista el archivo config.ini"""
    config_path = "config.ini"
    if not os.path.exists(config_path):
        print("❌ No se encontró el archivo config.ini")
        print("\nPor favor, crea un archivo config.ini con el siguiente contenido:")
        print("""
[postgresql]
host = localhost
port = 5432
database = itv_db
user = tu_usuario
password = tu_contraseña
        """)
        return False
    print("✅ Archivo config.ini encontrado")
    return True

def crear_esquema():
    """Crea el esquema de la base de datos"""
    try:
        from backend.almacen.database import crear_esquema
        print("\n📦 Creando esquema de base de datos...")
        crear_esquema()
        print("✅ Esquema de base de datos creado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al crear esquema: {e}")
        return False

def main():
    print("=" * 50)
    print("  Inicialización del Proyecto ITV")
    print("=" * 50)
    
    # Verificar configuración
    if not verificar_config():
        sys.exit(1)
    
    # Crear esquema
    if not crear_esquema():
        print("\n⚠️  Verifica que PostgreSQL esté corriendo y las credenciales sean correctas")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Inicialización completada")
    print("=" * 50)
    print("\nPuedes ejecutar la aplicación con: python main.py")
    print("O solo el servidor API con: python run_server.py")

if __name__ == "__main__":
    main()
