"""
API de búsqueda de estaciones ITV.

Este módulo proporciona endpoints REST para buscar estaciones ITV en la base de datos,
obtener listas de provincias y localidades disponibles.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.models import EstacionResponse, ProvinciaResponse, LocalidadResponse
from backend.almacen.database import conectar

router = APIRouter(
    prefix="/api",
    tags=["Búsqueda"],
    responses={
        500: {"description": "Error interno del servidor o de base de datos"}
    }
)

@router.get(
    "/buscar",
    response_model=List[EstacionResponse],
    summary="Buscar estaciones ITV",
    description="Busca estaciones ITV aplicando filtros opcionales. Todos los filtros son opcionales y se pueden combinar.",
    response_description="Lista de estaciones que cumplen los criterios de búsqueda, ordenadas por provincia, localidad y nombre"
)
async def buscar_estaciones(
    localidad: Optional[str] = Query(
        None,
        description="Nombre de la localidad (búsqueda parcial, case-insensitive)",
        examples=["Valencia"]
    ),
    codigo_postal: Optional[str] = Query(
        None,
        description="Código postal exacto (5 dígitos)",
        examples=["46001"],
        min_length=5,
        max_length=5
    ),
    provincia: Optional[str] = Query(
        None,
        description="Nombre de la provincia (búsqueda parcial, case-insensitive)",
        examples=["Valencia"]
    ),
    tipo: Optional[str] = Query(
        None,
        description="Tipo de estación",
        examples=["Estación_fija"],
        enum=["Estación_fija", "Estación_móvil", "Otros"]
    )
):
    """
    Busca estaciones ITV en la base de datos aplicando filtros opcionales.
    
    Este endpoint permite buscar estaciones utilizando uno o varios criterios de búsqueda.
    Los filtros de texto (localidad, provincia) utilizan búsqueda parcial case-insensitive.
    
    Args:
        localidad: Filtro opcional por nombre de localidad (búsqueda con LIKE)
        codigo_postal: Filtro opcional por código postal exacto
        provincia: Filtro opcional por nombre de provincia (búsqueda con LIKE)
        tipo: Filtro opcional por tipo de estación (exacto)
    
    Returns:
        List[EstacionResponse]: Lista de estaciones que cumplen los criterios,
            ordenadas alfabéticamente por provincia, localidad y nombre.
            Retorna lista vacía si no hay resultados.
    
    Raises:
        HTTPException: 
            - 500: Error al conectar con la base de datos o error en la consulta SQL
    
    Examples:
        - Buscar todas las estaciones: GET /api/buscar
        - Buscar por provincia: GET /api/buscar?provincia=Valencia
        - Buscar estaciones fijas en Valencia: GET /api/buscar?provincia=Valencia&tipo=Estación_fija
        - Buscar por código postal: GET /api/buscar?codigo_postal=46001
    """

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

@router.get(
    "/estaciones",
    response_model=List[EstacionResponse],
    summary="Obtener todas las estaciones",
    description="Retorna todas las estaciones disponibles sin filtros.",
    response_description="Lista completa de estaciones"
)
async def obtener_todas_estaciones():
    """
    Obtiene todas las estaciones ITV disponibles en la base de datos.
    
    Este endpoint es equivalente a buscar sin filtros, pero proporciona
    una URL semántica específica para obtener el catálogo completo.
    
    Returns:
        List[EstacionResponse]: Lista completa de estaciones.
    """
    return await buscar_estaciones(localidad=None, codigo_postal=None, provincia=None, tipo=None)

@router.get(
    "/provincias",
    response_model=List[ProvinciaResponse],
    summary="Obtener lista de provincias",
    description="Retorna todas las provincias disponibles en la base de datos",
    response_description="Lista de provincias ordenadas alfabéticamente por nombre"
)
async def obtener_provincias():
    """
    Obtiene la lista completa de provincias disponibles en la base de datos.
    
    Este endpoint es útil para poblar selectores/dropdowns en la interfaz de usuario.
    
    Returns:
        List[ProvinciaResponse]: Lista de provincias con su código y nombre,
            ordenadas alfabéticamente por nombre.
    
    Raises:
        HTTPException: 
            - 500: Error al conectar con la base de datos o error en la consulta
    
    Example:
        GET /api/provincias
        Response: [
            {"codigo": 1, "nombre": "A Coruña"},
            {"codigo": 2, "nombre": "Alicante"},
            ...
        ]
    """
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

@router.get(
    "/localidades/{provincia}",
    response_model=List[LocalidadResponse],
    summary="Obtener localidades de una provincia",
    description="Retorna todas las localidades de una provincia específica",
    response_description="Lista de localidades ordenadas alfabéticamente por nombre"
)
async def obtener_localidades(provincia: str):
    """
    Obtiene todas las localidades pertenecientes a una provincia específica.
    
    Este endpoint es útil para implementar selectores dependientes en la interfaz,
    donde primero se selecciona la provincia y luego se cargan sus localidades.
    
    Args:
        provincia: Nombre de la provincia (búsqueda exacta, case-insensitive)
    
    Returns:
        List[LocalidadResponse]: Lista de localidades con código, nombre y provincia,
            ordenadas alfabéticamente por nombre. Retorna lista vacía si la provincia
            no existe o no tiene localidades.
    
    Raises:
        HTTPException: 
            - 500: Error al conectar con la base de datos o error en la consulta
    
    Example:
        GET /api/localidades/Valencia
        Response: [
            {"codigo": 1, "nombre": "Valencia", "provincia": "Valencia"},
            {"codigo": 2, "nombre": "Torrent", "provincia": "Valencia"},
            ...
        ]
    """
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
