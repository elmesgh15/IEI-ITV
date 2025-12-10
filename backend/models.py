from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class TipoEstacion(str, Enum):
    FIJA = "Estación_fija"
    MOVIL = "Estación_móvil"
    OTROS = "Otros"

class EstacionResponse(BaseModel):
    cod_estacion: int
    nombre: str
    tipo: Optional[str] = None
    direccion: Optional[str] = None
    codigo_postal: Optional[str] = None
    longitud: Optional[float] = None
    latitud: Optional[float] = None
    descripcion: Optional[str] = None
    horario: Optional[str] = None
    contacto: Optional[str] = None
    url: Optional[str] = None
    localidad: str
    provincia: str

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

class EstadoAlmacenResponse(BaseModel):
    total_estaciones: int
    total_provincias: int
    total_localidades: int
    estaciones_por_tipo: dict
