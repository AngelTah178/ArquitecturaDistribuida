import time
from typing import List, Optional, Tuple
from database.mongo_manager import mongo_manager
from common.cluster_router import cluster_router
from modules.catalogos.schemas import PedidoCreateSchema, PedidoUpdateSchema


class CatalogoService:
    """Servicio que ejecuta la lógica de negocio CRUD contra MongoDB mediante enrutamiento dinámico."""

    def crear_pedido(self, datos: PedidoCreateSchema, user_id: str = "bot_1") -> Tuple[dict, str]:
        # Registrar actividad del usuario para escalamiento dinámico
        cluster_router.touch_user(user_id)
        cluster_id, cluster_name = cluster_router.get_target_cluster()

        # Calcular monto total
        total = sum(item.cantidad * item.precio for item in datos.productos)
        fecha = datos.fecha or time.strftime("%Y-%m-%d", time.localtime())
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        pedido_doc = {
            "cliente": datos.cliente.model_dump(),
            "productos": [p.model_dump() for p in datos.productos],
            "fecha": fecha,
            "total": round(total, 2),
            "cluster_origen": cluster_name,
            "sync_status": "PENDING",  # Pendiente para el servicio ETL
            "created_at": now_iso,
            "updated_at": now_iso,
            "created_by": user_id
        }

        # Guardar en el cluster de MongoDB seleccionado
        inserted_doc = mongo_manager.insert_pedido(cluster_id, pedido_doc)
        cluster_router.record_operation(cluster_name)
        return inserted_doc, cluster_name

    def listar_pedidos(self, cluster_id: Optional[int] = None) -> List[dict]:
        cid = cluster_id if cluster_id in (1, 2, 3) else None
        return mongo_manager.get_pedidos(cid)

    def obtener_pedido(self, pedido_id: str, cluster_id: Optional[int] = None) -> Optional[dict]:
        if cluster_id in (1, 2, 3):
            return mongo_manager.get_pedido_by_id(cluster_id, pedido_id)
        # Buscar en todos los clusters
        for cid in (1, 2, 3):
            doc = mongo_manager.get_pedido_by_id(cid, pedido_id)
            if doc:
                return doc
        return None

    def actualizar_pedido(self, pedido_id: str, updates: PedidoUpdateSchema, cluster_id: Optional[int] = None) -> bool:
        update_data = {k: v for k, v in updates.model_dump(exclude_unset=True).items() if v is not None}
        if "productos" in update_data:
            update_data["total"] = sum(p["cantidad"] * p["precio"] for p in update_data["productos"])

        clusters = [cluster_id] if cluster_id in (1, 2, 3) else [1, 2, 3]
        for cid in clusters:
            success = mongo_manager.update_pedido(cid, pedido_id, update_data)
            if success:
                cluster_name = f"Cluster Mongo #{cid}"
                cluster_router.record_operation(cluster_name)
                return True
        return False

    def eliminar_pedido(self, pedido_id: str, cluster_id: Optional[int] = None) -> bool:
        clusters = [cluster_id] if cluster_id in (1, 2, 3) else [1, 2, 3]
        for cid in clusters:
            success = mongo_manager.delete_pedido(cid, pedido_id)
            if success:
                cluster_name = f"Cluster Mongo #{cid}"
                cluster_router.record_operation(cluster_name)
                return True
        return False


catalogo_service = CatalogoService()
