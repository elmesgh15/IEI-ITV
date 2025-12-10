# Sistema de Gestión de Estaciones ITV

Aplicación de escritorio con backend REST API para gestionar estaciones de Inspección Técnica de Vehículos en España.

## 🚀 Características

- **Búsqueda de estaciones**: Filtrar por localidad, provincia, código postal y tipo
- **Visualización en mapa**: Marcadores interactivos con Leaflet
- **Carga de datos**: Importar datos de Galicia, Comunidad Valenciana y Catalunya
- **API REST**: FastAPI con endpoints para todas las operaciones
- **Interfaz moderna**: PySide6 (Qt) con diseño profesional

## 📋 Requisitos

- Python 3.8+
- PostgreSQL
- Google Chrome (para Selenium en extractores)

## 🔧 Instalación

### 1. Clonar el repositorio

```bash
cd Proyecto-IEI/IEI-ITV
```

### 2. Crear entorno virtual

```bash
python -m venv .venv
.venv\Scripts\activate  # En Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos

Crear archivo `config.ini` en la raíz del proyecto:

```ini
[postgresql]
host = localhost
port = 5432
database = itv_db
user = tu_usuario
password = tu_contraseña
```

### 5. Crear base de datos

```bash
# En PostgreSQL, crear la base de datos
createdb itv_db

# Inicializar el esquema
python init_project.py
```

## 🎮 Uso

### Ejecutar la aplicación completa

```bash
python main.py
```

Esto iniciará:

1. Servidor FastAPI en `http://127.0.0.1:8000`
2. Aplicación de escritorio Qt

### Ejecutar solo el servidor API

```bash
python run_server.py
```

Acceder a la documentación interactiva en: `http://127.0.0.1:8000/docs`

## 📖 Funcionalidades

### Pestaña Buscador

1. **Filtros disponibles**:

   - Localidad (búsqueda parcial)
   - Código Postal (exacto)
   - Provincia (búsqueda parcial)
   - Tipo (Estación Fija/Móvil)

2. **Resultados**:
   - Tabla con todas las estaciones encontradas
   - Mapa interactivo con marcadores
   - Click en marcador para ver detalles

### Pestaña Carga

1. **Seleccionar fuentes**:

   - ☑️ Galicia
   - ☑️ Comunitat Valenciana
   - ☑️ Catalunya

2. **Operaciones**:

   - **Cargar**: Importa datos de fuentes seleccionadas
   - **Borrar almacén**: Elimina todos los datos
   - **Cancelar**: Limpia el formulario

3. **Log de resultados**:
   - Número de registros insertados
   - Número de registros descartados
   - Detalles por fuente

## 🔌 API Endpoints

### Búsqueda

- `GET /api/buscar`: Buscar estaciones
  - Query params: `localidad`, `codigo_postal`, `provincia`, `tipo`
- `GET /api/provincias`: Listar provincias
- `GET /api/localidades/{provincia}`: Listar localidades de una provincia

### Carga de Datos

- `POST /api/cargar`: Cargar datos desde fuentes
  - Body: `{"galicia": bool, "valencia": bool, "catalunya": bool}`
- `DELETE /api/almacen`: Borrar todos los datos
- `GET /api/estado`: Obtener estadísticas del almacén

### Utilidades

- `GET /`: Información de la API
- `GET /health`: Estado del servidor

## 📁 Estructura del Proyecto

```
IEI-ITV/
├── backend/
│   ├── almacen/           # Conexión a PostgreSQL
│   │   └── database.py
│   ├── api/               # Endpoints FastAPI
│   │   ├── api_busqueda.py
│   │   └── api_carga.py
│   ├── extractores/       # Extracción de datos
│   │   ├── extractor_cv.py
│   │   ├── extractor_gal.py
│   │   └── extractor_cat.py
│   ├── wrappers/          # Wrappers para extractores
│   │   ├── wrapper_cv.py
│   │   ├── wrapper_gal.py
│   │   └── wrapper_cat.py
│   ├── models.py          # Modelos Pydantic
│   └── server.py          # Aplicación FastAPI
├── frontend/
│   ├── componentes/
│   │   └── mapa.py        # Widget de mapa Leaflet
│   ├── ventanas/
│   │   ├── ventana_busqueda.py
│   │   └── ventana_carga.py
│   ├── api_client.py      # Cliente HTTP Qt
│   └── main_window.py     # Ventana principal
├── datos/                 # Archivos de datos
├── main.py               # Punto de entrada
├── run_server.py         # Ejecutar solo API
├── init_project.py       # Script de inicialización
├── config.ini            # Configuración DB (gitignored)
└── requirements.txt
```

## 🛠️ Desarrollo

### Modo desarrollo del servidor

El servidor se iniciará con auto-reload:

```bash
python run_server.py
```

### Probar endpoints con curl

```bash
# Obtener provincias
curl http://127.0.0.1:8000/api/provincias

# Buscar estaciones en Valencia
curl "http://127.0.0.1:8000/api/buscar?provincia=Valencia"

# Cargar datos
curl -X POST http://127.0.0.1:8000/api/cargar \
  -H "Content-Type: application/json" \
  -d '{"valencia": true}'
```

## ⚠️ Notas Importantes

1. **Primera ejecución**: Ejecutar `python init_project.py` para crear el esquema
2. **Carga de datos**: La primera carga puede tardar varios minutos (especialmente Valencia por Selenium)
3. **Selenium**: El extractor de Valencia usa Selenium y requiere Chrome instalado
4. **PostgreSQL**: Debe estar corriendo antes de iniciar la aplicación

## 🐛 Solución de Problemas

### Error de conexión a base de datos

- Verificar que PostgreSQL esté corriendo
- Revisar credenciales en `config.ini`
- Verificar que la base de datos existe: `psql -l`

### Error "No module named..."

- Activar el entorno virtual
- Reinstalar dependencias: `pip install -r requirements.txt`

### Mapa no carga

- Verificar conexión a internet (usa CDN de Leaflet)
- Revisar consola del navegador en DevTools

## 📝 Licencia

Proyecto académico - IEI
