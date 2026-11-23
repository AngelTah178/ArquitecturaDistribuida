from typing import List, Optional
from pydantic import BaseModel, Field


class ClienteSchema(BaseModel):
    nombre: str = Field(..., description="Nombre completo del cliente", examples=["Juan Perez"])
    correo: str = Field(..., description="Correo electrónico del cliente", examples=["juan@mail.com"])
    telefono: Optional[str] = Field(default=None, description="Teléfono de contacto", examples=["9981234567"])


class ItemProductoSchema(BaseModel):
    id: Optional[int] = Field(default=1, examples=[1])
    sku: Optional[str] = Field(default=None, examples=["PROD-001"])
    nombre: Optional[str] = Field(default="Sensor IoT", examples=["Sensor IoT de Temperatura"])
    cantidad: int = Field(..., gt=0, examples=[2])
    precio: float = Field(..., ge=0, examples=[450.00])


class PedidoCreateSchema(BaseModel):
    cliente: ClienteSchema
    productos: List[ItemProductoSchema]
    fecha: Optional[str] = Field(default=None, examples=["2026-10-01"])


class PedidoUpdateSchema(BaseModel):
    cliente: Optional[ClienteSchema] = None
    productos: Optional[List[ItemProductoSchema]] = None
    fecha: Optional[str] = None


class PedidoResponseSchema(BaseModel):
    id: str
    cliente: ClienteSchema
    productos: List[ItemProductoSchema]
    fecha: str
    total: float
    cluster_origen: str
    sync_status: str
    created_at: str
