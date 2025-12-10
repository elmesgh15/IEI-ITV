from fastapi import APIRouter, HTTPException
from backend.models import CargaRequest, CargaResponse, EstadoAlmacenResponse
from backend.almacen.database import conectar
from backend.wrappers.wrapper_cv import ejecutar_carga_cv
from backend.wrappers.wrapper_gal import ejecutar_carga_gal
from backend.wrappers.wrapper_cat import ejecutar_carga_cat
import asyncio
from concurrent.futures import ThreadPoolExecutor

router = APIRouter(prefix="/api", tags=["carga"])

# Executor para tareas de carga en background
executor = ThreadPoolExecutor(max_workers=1)

@router.post("/cargar", response_model=CargaResponse)
async def cargar_datos(request: CargaRequest):
    """
    Ejecuta la carga de datos desde las fuentes seleccionadas.
    Este proceso puede tardar varios minutos dependiendo de las fuentes seleccionadas.
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
        # Ejecutar carga de Comunidad Valenciana
        if request.valencia:
            try:
                resultado = await asyncio.get_event_loop().run_in_executor(
                    executor, ejecutar_carga_cv
                )
                total_insertados += resultado.get('insertados', 0)
                total_descartados += resultado.get('descartados', 0)
                detalles['valencia'] = resultado
                mensajes.append(f"Valencia: {resultado.get('insertados', 0)} insertados, {resultado.get('descartados', 0)} descartados")
            except Exception as e:
                mensajes.append(f"Error en Valencia: {str(e)}")
                detalles['valencia'] = {'error': str(e)}
        
        # Ejecutar carga de Galicia
        if request.galicia:
            try:
                resultado = await asyncio.get_event_loop().run_in_executor(
                    executor, ejecutar_carga_gal
                )
                total_insertados += resultado.get('insertados', 0)
                total_descartados += resultado.get('descartados', 0)
                detalles['galicia'] = resultado
                mensajes.append(f"Galicia: {resultado.get('insertados', 0)} insertados, {resultado.get('descartados', 0)} descartados")
            except Exception as e:
                mensajes.append(f"Error en Galicia: {str(e)}")
                detalles['galicia'] = {'error': str(e)}
        
        # Ejecutar carga de Catalunya
        if request.catalunya:
            try:
                resultado = await asyncio.get_event_loop().run_in_executor(
                    executor, ejecutar_carga_cat
                )
                total_insertados += resultado.get('insertados', 0)
                total_descartados += resultado.get('descartados', 0)
                detalles['catalunya'] = resultado
                mensajes.append(f"Catalunya: {resultado.get('insertados', 0)} insertados, {resultado.get('descartados', 0)} descartados")
            except Exception as e:
                mensajes.append(f"Error en Catalunya: {str(e)}")
                detalles['catalunya'] = {'error': str(e)}
        
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

@router.delete("/almacen")
async def borrar_almacen():
    """
    Borra todos los datos del almacén (estaciones, localidades y provincias).
    """
    conn = conectar()
    if not conn:
        raise HTTPException(status_code=500, detail="Error al conectar con la base de datos")
    
    try:
        cur = conn.cursor()
        
        # Borrar en orden inverso debido a las foreign keys
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

@router.get("/estado", response_model=EstadoAlmacenResponse)
async def obtener_estado():
    """
    Obtiene estadísticas del estado actual del almacén de datos.
    """
    conn = conectar()
    if not conn:
        raise HTTPException(status_code=500, detail="Error al conectar con la base de datos")
    
    try:
        cur = conn.cursor()
        
        # Total de estaciones
        cur.execute("SELECT COUNT(*) FROM Estacion")
        total_estaciones = cur.fetchone()[0]
        
        # Total de provincias
        cur.execute("SELECT COUNT(*) FROM Provincia")
        total_provincias = cur.fetchone()[0]
        
        # Total de localidades
        cur.execute("SELECT COUNT(*) FROM Localidad")
        total_localidades = cur.fetchone()[0]
        
        # Estaciones por tipo
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
