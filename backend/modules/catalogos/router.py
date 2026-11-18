from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Query, status
from modules.catalogos.schemas import (
    PedidoCreateSchema,
    PedidoUpdateSchema,
    PedidoResponseSchema
)
from modules.catalogos.service import catalogo_service
from common.cluster_router import cluster_router

router = APIRouter(prefix="/api/v1/pedidos", tags=["Catálogos (CRUD)"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Crear Pedido (Redirección dinámica a Cluster Mongo)")
def crear_pedido(
    pedido: PedidoCreateSchema,
    x_user: Optional[str] = Header(default="bot_1", description="ID de usuario/bot para cálculo de carga dinámica")
):
    """
    Inserta un nuevo pedido. 
    Detecta automáticamente los usuarios activos y redirige al cluster correspondiente:
      - 1-3 usuarios: Cluster Mongo #1
      - 4-6 usuarios: Cluster Mongo #2
      - 7-9 usuarios: Cluster Mongo #3
    """
    doc, cluster_utilizado = catalogo_service.crear_pedido(pedido, user_id=x_user)
    return {
        "mensaje": "Pedido registrado exitosamente",
        "cluster_utilizado": cluster_utilizado,
        "usuarios_activos": cluster_router.get_active_users_count(),
        "pedido": doc
    }


@router.get("", summary="Listar Pedidos")
def listar_pedidos(
    cluster_id: Optional[int] = Query(default=None, ge=1, le=3, description="Filtrar por cluster específico (1, 2 o 3)")
):
    """Retorna la lista de pedidos de MongoDB."""
    pedidos = catalogo_service.listar_pedidos(cluster_id)
    return {
        "total": len(pedidos),
        "cluster_filtro": f"Cluster Mongo #{cluster_id}" if cluster_id else "Todos los clusters",
        "pedidos": pedidos
    }


@router.get("/{pedido_id}", summary="Consultar Pedido por ID")
def obtener_pedido(pedido_id: str, cluster_id: Optional[int] = Query(default=None, ge=1, le=3)):
    """Obtiene un pedido específico por su ID."""
    pedido = catalogo_service.obtener_pedido(pedido_id, cluster_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    return pedido


@router.put("/{pedido_id}", summary="Actualizar Pedido")
def actualizar_pedido(
    pedido_id: str,
    updates: PedidoUpdateSchema,
    cluster_id: Optional[int] = Query(default=None, ge=1, le=3)
):
    """Actualiza la información de un pedido existente y lo marca como pendiente de sincronización."""
    exito = catalogo_service.actualizar_pedido(pedido_id, updates, cluster_id)
    if not exito:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado para actualizar")
    return {"mensaje": "Pedido actualizado con éxito", "sync_status": "PENDING"}


@router.delete("/{pedido_id}", summary="Eliminar Pedido")
def eliminar_pedido(pedido_id: str, cluster_id: Optional[int] = Query(default=None, ge=1, le=3)):
    """Elimina un pedido del cluster indicado."""
    exito = catalogo_service.eliminar_pedido(pedido_id, cluster_id)
    if not exito:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado para eliminar")
    return {"mensaje": "Pedido eliminado correctamente"}
