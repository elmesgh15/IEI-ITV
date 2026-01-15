"""
Modelos de datos Pydantic para la API de estaciones ITV.

Define los esquemas de datos utilizados en los endpoints de FastAPI para:
- Validación automática de requests y responses
- Generación de documentación OpenAPI/Swagger
- Serialización/deserialización JSON

Todos los modelos heredan de BaseModel de Pydantic y utilizan type hints
para validación de tipos en tiempo de ejecución.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum

class TipoEstacion(str, Enum):
    FIJA = "Estación_fija"
    MOVIL = "Estación_móvil"
    OTROS = "Otros"

class EstacionResponse(BaseModel):
    """
    Modelo de respuesta para una estación ITV.
    
    Representa todos los datos de una estación incluyendo ubicación,
    información de contacto y relaciones con localidad y provincia.
    """
    cod_estacion: int = Field(..., description="ID único de la estación")
    nombre: str = Field(..., description="Nombre oficial de la estación")
    tipo: Optional[str] = Field(None, description="Tipo de estación: Estación_fija, Estación_móvil, Otros")
    direccion: Optional[str] = Field(None, description="Dirección física completa")
    codigo_postal: Optional[str] = Field(None, description="Código postal (5 dígitos)")
    longitud: Optional[float] = Field(None, description="Coordenada GPS longitud (formato decimal)")
    latitud: Optional[float] = Field(None, description="Coordenada GPS latitud (formato decimal)")
    descripcion: Optional[str] = Field(None, description="Descripción adicional de la estación")
    horario: Optional[str] = Field(None, description="Horario de atención")
    contacto: Optional[str] = Field(None, description="Información de contacto (teléfono, email)")
    url: Optional[str] = Field(None, description="Sitio web de la estación o servicio")
    localidad: str = Field(..., description="Nombre de la localidad/municipio")
    provincia: str = Field(..., description="Nombre de la provincia")

class BusquedaRequest(BaseModel):
    localidad: Optional[str] = None
    codigo_postal: Optional[str] = None
    provincia: Optional[str] = None
    tipo: Optional[str] = None

class ProvinciaResponse(BaseModel):
    codigo: int
    nombre: str

class LocalidadResponse(BaseModel):
    codigo: int
    nombre: str
    provincia: str

class CargaRequest(BaseModel):
    galicia: bool = False
    valencia: bool = False
    catalunya: bool = False

class CargaResponse(BaseModel):
    success: bool
    mensaje: str
    insertados: int = 0
    descartados: int = 0
    detalles: Optional[dict] = None

class WrapperResponse(BaseModel):
    success: bool
    insertados: int
    descartados: int
    log: str
    error: Optional[str] = None

class EstadoAlmacenResponse(BaseModel):
    total_estaciones: int
    total_provincias: int
    total_localidades: int
    estaciones_por_tipo: dict
