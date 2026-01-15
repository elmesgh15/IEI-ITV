"""
Servidor FastAPI principal para la API de estaciones ITV.

Este módulo configura y ejecuta el servidor FastAPI que proporciona:
- Endpoints REST para búsqueda de estaciones
- Endpoints para carga de datos desde archivos fuente
- Gestión del almacén de datos (borrado, estadísticas)
- Documentación interactiva OpenAPI/Swagger en /docs

El servidor incluye middleware CORS para permitir peticiones desde el frontend Qt.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.api_busqueda import router as busqueda_router
from backend.api.api_carga import router as carga_router

app = FastAPI(
    title="API de Estaciones ITV",
    description="""
    API REST para gestión de estaciones de Inspección Técnica de Vehículos (ITV) en España.
    
    ## Funcionalidades
    
    * **Búsqueda de estaciones**: Buscar por localidad, código postal, provincia o tipo
    * **Carga de datos**: Importar datos desde archivos CSV, XML y JSON
    * **Gestión de datos**: Borrar almacén y obtener estadísticas
    * **Catálogos**: Listar provincias y localidades disponibles
    
    ## Comunidades Autónomas Soportadas
    
    * Galicia (GAL)
    * Comunidad Valenciana (CV)
    * Cataluña (CAT)
    
    ## Documentación
    
    * **Swagger UI**: /docs (esta página)
    * **ReDoc**: /redoc
    * **OpenAPI Schema**: /openapi.json
    """,
    version="1.0.0",
    contact={
        "name": "Proyecto IEI-ITV",
    },
    license_info={
        "name": "MIT",
    },
)

# Configurar CORS para permitir conexiones desde la aplicación Qt
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.wrappers.wrapper_gal import router as gal_router
from backend.wrappers.wrapper_cat import router as cat_router
from backend.wrappers.wrapper_cv import router as cv_router

# Registrar routers
app.include_router(busqueda_router)
app.include_router(carga_router)
app.include_router(gal_router, prefix="/api/wrapper/gal", tags=["wrapper-galicia"])
app.include_router(cat_router, prefix="/api/wrapper/cat", tags=["wrapper-catalunya"])
app.include_router(cv_router, prefix="/api/wrapper/cv", tags=["wrapper-valencia"])

@app.get("/")
async def root():
    return {
        "mensaje": "API ITV funcionando correctamente",
        "version": "1.0.0",
        "endpoints": {
            "busqueda": "/api/buscar",
            "provincias": "/api/provincias",
            "localidades": "/api/localidades/{provincia}",
            "cargar": "/api/cargar",
            "borrar": "/api/almacen",
            "estado": "/api/estado"
        }
    }

@app.get("/health")
async def health():
    """Endpoint de salud para verificar que el servidor está activo"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
