from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.models import EstacionResponse, ProvinciaResponse, LocalidadResponse
from backend.almacen.database import conectar

router = APIRouter(prefix="/api", tags=["busqueda"])

@router.get("/buscar", response_model=List[EstacionResponse])
async def buscar_estaciones(
    localidad: Optional[str] = Query(None),
    codigo_postal: Optional[str] = Query(None),
    provincia: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None)
):

    conn = conectar()
    if not conn:
        raise HTTPException(status_code=500, detail="Error al conectar con la base de datos")
    
    try:
        cur = conn.cursor()
        query = """
            SELECT 
                e.cod_estacion, e.nombre, e.tipo, e.direccion, e.codigo_postal,
                e.longitud, e.latitud, e.descripcion, e.horario, e.contacto, e.url,
                l.nombre as localidad_nombre, p.nombre as provincia_nombre
            FROM Estacion e
            JOIN Localidad l ON e.codigo_localidad = l.codigo
            JOIN Provincia p ON l.codigo_provincia = p.codigo
            WHERE 1=1
        """
        params = []
        
        if localidad:
            query += " AND LOWER(l.nombre) LIKE LOWER(%s)"
            params.append(f"%{localidad}%")
        
        if codigo_postal:
            query += " AND e.codigo_postal = %s"
            params.append(codigo_postal)
        
        if provincia:
            query += " AND LOWER(p.nombre) LIKE LOWER(%s)"
            params.append(f"%{provincia}%")
        
        if tipo:
            query += " AND e.tipo = %s"
            params.append(tipo)
        
        query += " ORDER BY p.nombre, l.nombre, e.nombre"
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        estaciones = []
        for row in rows:
            estaciones.append(EstacionResponse(
                cod_estacion=row[0],
                nombre=row[1],
                tipo=row[2],
                direccion=row[3],
                codigo_postal=row[4],
                longitud=row[5],
                latitud=row[6],
                descripcion=row[7],
                horario=row[8],
                contacto=row[9],
                url=row[10],
                localidad=row[11],
                provincia=row[12]
            ))
        
        return estaciones
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda: {str(e)}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/provincias", response_model=List[ProvinciaResponse])
async def obtener_provincias():
    conn = conectar()
    if not conn:
        raise HTTPException(status_code=500, detail="Error al conectar con la base de datos")
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT codigo, nombre FROM Provincia ORDER BY nombre")
        rows = cur.fetchall()
        
        provincias = [ProvinciaResponse(codigo=row[0], nombre=row[1]) for row in rows]
        return provincias
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener provincias: {str(e)}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/localidades/{provincia}", response_model=List[LocalidadResponse])
async def obtener_localidades(provincia: str):
    conn = conectar()
    if not conn:
        raise HTTPException(status_code=500, detail="Error al conectar con la base de datos")
    
    try:
        cur = conn.cursor()
        query = """
            SELECT l.codigo, l.nombre, p.nombre as provincia_nombre
            FROM Localidad l
            JOIN Provincia p ON l.codigo_provincia = p.codigo
            WHERE LOWER(p.nombre) = LOWER(%s)
            ORDER BY l.nombre
        """
        cur.execute(query, (provincia,))
        rows = cur.fetchall()
        
        localidades = [
            LocalidadResponse(codigo=row[0], nombre=row[1], provincia=row[2]) 
            for row in rows
        ]
        return localidades
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener localidades: {str(e)}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
