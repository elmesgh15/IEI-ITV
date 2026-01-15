"""
API de carga de datos de estaciones ITV.

Este módulo proporciona endpoints REST para:
- Cargar datos de estaciones desde archivos fuente (CSV, XML, JSON)
- Borrar todos los datos del almacén
- Obtener estadísticas del estado actual de la base de datos

La carga de datos se realiza de forma asíncrona y paralela para múltiples comunidades.
"""

from fastapi import APIRouter, HTTPException
from backend.models import CargaRequest, CargaResponse, EstadoAlmacenResponse
from backend.almacen.database import conectar
import httpx
import asyncio

router = APIRouter(
    prefix="/api",
    tags=["Carga de Datos"],
    responses={
        500: {"description": "Error interno del servidor o de base de datos"}
    }
)

async def call_wrapper(url: str):
    """
    Realiza una petición HTTP POST asíncrona a un wrapper de extractor.
    
    Args:
        url: URL completa del endpoint del wrapper
    
    Returns:
        dict: Respuesta JSON del wrapper con estadísticas de carga
    
    Raises:
        httpx.HTTPStatusError: Si la petición HTTP falla
    """
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(url)
        response.raise_for_status()
        return response.json()

@router.post(
    "/cargar",
    response_model=CargaResponse,
    summary="Cargar datos de estaciones ITV",
    description="Carga datos de estaciones desde archivos fuente de las comunidades seleccionadas. La carga se realiza en paralelo.",
    response_description="Resumen de la carga con estadísticas por comunidad"
)
async def cargar_datos(request: CargaRequest):
    """
    Carga datos de estaciones ITV desde archivos fuente.
    
    Este endpoint ejecuta los extractores de las comunidades seleccionadas de forma
    asíncrona y paralela. Cada extractor:
    1. Lee su archivo fuente (CSV/XML/JSON)
    2. Valida y limpia los datos
    3. Inserta registros válidos en la base de datos
    4. Descarta registros inválidos con logging detallado
    
    Args:
        request: Objeto con flags booleanos para cada comunidad (galicia, valencia, catalunya)
    
    Returns:
        CargaResponse: Objeto con:
            - success: True si al menos una comunidad se cargó sin errores
            - mensaje: Resumen textual de los resultados
            - insertados: Total de registros insertados
            - descartados: Total de registros descartados
            - detalles: Diccionario con resultados por comunidad
    
    Raises:
        HTTPException:
            - 400: Si no se selecciona ninguna comunidad
            - 500: Si hay un error crítico en el proceso de carga
    
    Example:
        POST /api/cargar
        Body: {"galicia": true, "valencia": true, "catalunya": false}
        
        Response: {
            "success": true,
            "mensaje": "Valencia: 50 insertados, 5 descartados\\nGalicia: 30 insertados, 2 descartados",
            "insertados": 80,
            "descartados": 7,
            "detalles": {
                "valencia": {"insertados": 50, "descartados": 5, "log": "..."},
                "galicia": {"insertados": 30, "descartados": 2, "log": "..."}
            }
        }
    
    Note:
        El proceso puede tardar varios minutos dependiendo del tamaño de los archivos
        y la cantidad de comunidades seleccionadas. El timeout está configurado a 300 segundos.
    """

    if not (request.galicia or request.valencia or request.catalunya):
        raise HTTPException(
            status_code=400, 
            detail="Debe seleccionar al menos una fuente de datos"
        )
    
    total_insertados = 0
    total_descartados = 0
    mensajes = []
    detalles = {}
    
    try:
        tasks = []
        labels = []

        if request.valencia:
            tasks.append(call_wrapper("http://127.0.0.1:8000/api/wrapper/cv/cargar"))
            labels.append("valencia")
        
        if request.galicia:
            tasks.append(call_wrapper("http://127.0.0.1:8000/api/wrapper/gal/cargar"))
            labels.append("galicia")
        
        if request.catalunya:
            tasks.append(call_wrapper("http://127.0.0.1:8000/api/wrapper/cat/cargar"))
            labels.append("catalunya")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for label, result in zip(labels, results):
            if isinstance(result, Exception):
                mensajes.append(f"Error en {label.capitalize()}: {str(result)}")
                detalles[label] = {'error': str(result)}
            else:
                insertados = result.get('insertados', 0)
                descartados = result.get('descartados', 0)
                total_insertados += insertados
                total_descartados += descartados
                detalles[label] = result
                mensajes.append(f"{label.capitalize()}: {insertados} insertados, {descartados} descartados")
        
        mensaje_final = "\n".join(mensajes)
        
        return CargaResponse(
            success=True,
            mensaje=mensaje_final,
            insertados=total_insertados,
            descartados=total_descartados,
            detalles=detalles
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la carga de datos: {str(e)}")

@router.delete(
    "/almacen",
    summary="Borrar todos los datos del almacén",
    description="Elimina todas las estaciones, localidades y provincias de la base de datos",
    response_description="Confirmación del borrado con cantidad de registros eliminados"
)
async def borrar_almacen():
    """
    Borra todos los datos del almacén de forma permanente.
    
    Este endpoint elimina todos los registros de las tablas:
    - Estacion
    - Localidad
    - Provincia
    
    Las eliminaciones se realizan en orden para respetar las restricciones
    de integridad referencial (foreign keys con CASCADE).
    
    Returns:
        dict: Objeto con:
            - success: True si el borrado fue exitoso
            - mensaje: Mensaje de confirmación
            - detalles: Diccionario con cantidad de registros borrados por tabla
    
    Raises:
        HTTPException:
            - 500: Si hay error de conexión o en la operación de borrado
    
    Warning:
        Esta operación es IRREVERSIBLE. Todos los datos se perderán permanentemente.
    
    Example:
        DELETE /api/almacen
        
        Response: {
            "success": true,
            "mensaje": "Almacén borrado correctamente",
            "detalles": {
                "estaciones_borradas": 150,
                "localidades_borradas": 45,
                "provincias_borradas": 12
            }
        }
    """

    conn = conectar()
    if not conn:
        raise HTTPException(status_code=500, detail="Error al conectar con la base de datos")
    
    try:
        cur = conn.cursor()
        
        cur.execute("DELETE FROM Estacion")
        estaciones_borradas = cur.rowcount
        
        cur.execute("DELETE FROM Localidad")
        localidades_borradas = cur.rowcount
        
        cur.execute("DELETE FROM Provincia")
        provincias_borradas = cur.rowcount
        
        conn.commit()
        
        return {
            "success": True,
            "mensaje": f"Almacén borrado correctamente",
            "detalles": {
                "estaciones_borradas": estaciones_borradas,
                "localidades_borradas": localidades_borradas,
                "provincias_borradas": provincias_borradas
            }
        }
    
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al borrar el almacén: {str(e)}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get(
    "/estado",
    response_model=EstadoAlmacenResponse,
    summary="Obtener estado del almacén",
    description="Retorna estadísticas actuales de la base de datos",
    response_description="Estadísticas completas del almacén"
)
async def obtener_estado():
    """
    Obtiene estadísticas actuales del almacén de datos.
    
    Este endpoint proporciona información sobre el estado actual de la base de datos,
    útil para dashboards y verificación del sistema.
    
    Returns:
        EstadoAlmacenResponse: Objeto con:
            - total_estaciones: Cantidad total de estaciones
            - total_provincias: Cantidad de provincias únicas
            - total_localidades: Cantidad de localidades únicas
            - estaciones_por_tipo: Diccionario con conteo por tipo de estación
    
    Raises:
        HTTPException:
            - 500: Si hay error de conexión o en las consultas
    
    Example:
        GET /api/estado
        
        Response: {
            "total_estaciones": 150,
            "total_provincias": 12,
            "total_localidades": 45,
            "estaciones_por_tipo": {
                "Estación_fija": 140,
                "Estación_móvil": 8,
                "Otros": 2
            }
        }
    """

    conn = conectar()
    if not conn:
        raise HTTPException(status_code=500, detail="Error al conectar con la base de datos")
    
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM Estacion")
        total_estaciones = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM Provincia")
        total_provincias = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM Localidad")
        total_localidades = cur.fetchone()[0]
        
        cur.execute("""
            SELECT tipo, COUNT(*) 
            FROM Estacion 
            GROUP BY tipo
        """)
        tipos = cur.fetchall()
        estaciones_por_tipo = {tipo: count for tipo, count in tipos}
        
        return EstadoAlmacenResponse(
            total_estaciones=total_estaciones,
            total_provincias=total_provincias,
            total_localidades=total_localidades,
            estaciones_por_tipo=estaciones_por_tipo
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estado: {str(e)}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
