import time
import logging
from typing import Dict, Any, List
from database.mongo_manager import mongo_manager
from database.postgres_manager import postgres_manager

logger = logging.getLogger("ETL_SyncService")


class ETLService:
    """
    Servicio de Sincronización ETL:
      1. Extraer: Documentos nuevos o modificados en MongoDB (sync_status == 'PENDING').
      2. Transformar: Desanida estructuras JSON NoSQL a modelo 3FN (clientes, pedidos, detalle_pedido).
      3. Cargar: Inserta o actualiza en PostgreSQL (Neon) garantizando integridad y trazabilidad.
    """

    def __init__(self):
        self.is_running = False
        self.last_sync_time = "Nunca"
        self.last_status = "SINCRONIZADO"  # 'SINCRONIZADO', 'EN_EJECUCION', 'ERROR'
        self.total_extraidos_acumulado = 0
        self.total_cargados_acumulado = 0
        self.last_error_message = ""

    def run_pipeline(self) -> Dict[str, Any]:
        """Ejecuta el ciclo completo del ETL."""
        if self.is_running:
            return {"estado": "EN_EJECUCION", "mensaje": "Un proceso de sincronización ya está en curso"}

        self.is_running = True
        self.last_status = "EN_EJECUCION"
        start_time = time.time()
        resumen = {
            "cluster_1": {"extraidos": 0, "cargados": 0},
            "cluster_2": {"extraidos": 0, "cargados": 0},
            "cluster_3": {"extraidos": 0, "cargados": 0},
            "total_extraidos": 0,
            "total_cargados": 0,
            "estado": "SINCRONIZADO",
            "tiempo_ms": 0
        }

        try:
            logger.info("Iniciando ciclo de sincronización ETL (MongoDB -> PostgreSQL Neon)...")

            # Iterar sobre los 3 clusters de MongoDB
            for cid in (1, 2, 3):
                cluster_name = f"Cluster Mongo #{cid}"
                pedidos = mongo_manager.get_pedidos(cluster_id=cid)
                # Extraer pendientes
                pendientes = [p for p in pedidos if p.get("sync_status") != "SYNCED"]

                resumen[f"cluster_{cid}"]["extraidos"] = len(pendientes)
                resumen["total_extraidos"] += len(pendientes)

                synced_ids = []
                cargados_cluster = 0

                for doc in pendientes:
                    try:
                        # 1. Transformar y cargar CLIENTE (Evitar duplicados con upsert por correo)
                        cliente_data = doc.get("cliente", {})
                        nombre_cliente = cliente_data.get("nombre", "Cliente Desconocido")
                        correo_cliente = cliente_data.get("correo", f"cliente_{int(time.time())}@mail.com")
                        tel_cliente = cliente_data.get("telefono")

                        cliente_id = postgres_manager.upsert_cliente(
                            nombre=nombre_cliente,
                            correo=correo_cliente,
                            telefono=tel_cliente
                        )

                        # 2. Transformar y cargar PEDIDO (Evitar duplicados con mongo_id unique)
                        mongo_id = str(doc.get("_id"))
                        fecha_pedido = doc.get("fecha", time.strftime("%Y-%m-%d"))
                        total_pedido = float(doc.get("total", 0.0))

                        pedido_id = postgres_manager.insert_pedido(
                            cliente_id=cliente_id,
                            fecha=fecha_pedido,
                            mongo_id=mongo_id,
                            cluster_origen=cid,
                            total=total_pedido
                        )

                        # 3. Transformar y cargar DETALLE_PEDIDO
                        productos_list = doc.get("productos", [])
                        for prod in productos_list:
                            prod_nombre = prod.get("nombre", "Producto Estándar")
                            prod_precio = float(prod.get("precio", 100.0))
                            prod_sku = prod.get("sku")
                            prod_id = postgres_manager.get_or_create_producto(
                                nombre=prod_nombre,
                                precio=prod_precio,
                                sku=prod_sku
                            )

                            cantidad = int(prod.get("cantidad", 1))
                            postgres_manager.insert_detalle_pedido(
                                pedido_id=pedido_id,
                                producto_id=prod_id,
                                cantidad=cantidad,
                                precio_unitario=prod_precio
                            )

                        synced_ids.append(mongo_id)
                        cargados_cluster += 1
                    except Exception as item_err:
                        logger.error(f"Error transformando/cargando pedido {doc.get('_id')}: {item_err}")

                # Marcar documentos sincronizados en MongoDB
                if synced_ids:
                    mongo_manager.mark_pedidos_synced(cid, synced_ids)

                resumen[f"cluster_{cid}"]["cargados"] = cargados_cluster
                resumen["total_cargados"] += cargados_cluster

                # Registrar auditoría en sync_logs
                tiempo_cluster = int((time.time() - start_time) * 1000)
                postgres_manager.insert_sync_log(
                    cluster_origen=cluster_name,
                    extraidos=len(pendientes),
                    cargados=cargados_cluster,
                    estado="SINCRONIZADO" if cargados_cluster == len(pendientes) else "PARCIAL",
                    tiempo_ms=tiempo_cluster,
                    mensaje=f"Sincronizados {cargados_cluster} de {len(pendientes)} registros"
                )

            total_ms = int((time.time() - start_time) * 1000)
            resumen["tiempo_ms"] = total_ms
            self.last_status = "SINCRONIZADO"
            self.last_sync_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.total_extraidos_acumulado += resumen["total_extraidos"]
            self.total_cargados_acumulado += resumen["total_cargados"]
            logger.info(f"Sincronización ETL completada: {resumen['total_cargados']} registros cargados en {total_ms} ms.")
            return resumen

        except Exception as e:
            self.last_status = "ERROR"
            self.last_error_message = str(e)
            logger.error(f"Falla crítica en servicio ETL: {e}")
            resumen["estado"] = "ERROR"
            resumen["error"] = str(e)
            postgres_manager.insert_sync_log(
                cluster_origen="ALL",
                extraidos=resumen["total_extraidos"],
                cargados=resumen["total_cargados"],
                estado="ERROR",
                tiempo_ms=int((time.time() - start_time) * 1000),
                mensaje=str(e)
            )
            return resumen
        finally:
            self.is_running = False

    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado de la sincronización para las tarjetas del Dashboard y la API."""
        return {
            "estado": self.last_status,
            "en_ejecucion": self.is_running,
            "ultima_sincronizacion": self.last_sync_time,
            "intervalo_minutos": 3,
            "total_extraidos_acumulado": self.total_extraidos_acumulado,
            "total_cargados_acumulado": self.total_cargados_acumulado,
            "ultimo_error": self.last_error_message
        }


etl_service = ETLService()
