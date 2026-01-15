from fastapi import APIRouter, HTTPException
from backend.models import CargaRequest, CargaResponse, EstadoAlmacenResponse
from backend.almacen.database import conectar
import httpx
import asyncio

router = APIRouter(prefix="/api", tags=["carga"])

async def call_wrapper(url: str):
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(url)
        response.raise_for_status()
        return response.json()

@router.post("/cargar", response_model=CargaResponse)
async def cargar_datos(request: CargaRequest):

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

@router.delete("/almacen")
async def borrar_almacen():

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

@router.get("/estado", response_model=EstadoAlmacenResponse)
async def obtener_estado():

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
