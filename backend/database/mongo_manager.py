import time
import logging
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ConnectionFailure

from core.config import settings

logger = logging.getLogger("MongoClusterManager")


class MongoClusterManager:
    """
    Gestiona la conexión, operaciones y estado de los 3 Clusters de MongoDB Atlas:
      - Cluster #1
      - Cluster #2
      - Cluster #3
    Incluye fallback resiliente para pruebas locales cuando no hay conexión a internet o Atlas.
    """

    def __init__(self):
        self.uris = {
            1: settings.MONGO_CLUSTER_1_URI,
            2: settings.MONGO_CLUSTER_2_URI,
            3: settings.MONGO_CLUSTER_3_URI,
        }
        self.db_name = settings.MONGO_DB_NAME
        self.clients: Dict[int, Optional[MongoClient]] = {1: None, 2: None, 3: None}
        self.is_connected: Dict[int, bool] = {1: False, 2: False, 3: False}
        self.latencies: Dict[int, float] = {1: 0.0, 2: 0.0, 3: 0.0}

        # Almacenamiento local en memoria como fallback / mock para desarrollo local
        self._mock_storage: Dict[int, Dict[str, List[dict]]] = {
            1: {"pedidos": [], "auditoria_operaciones": []},
            2: {"pedidos": [], "auditoria_operaciones": []},
            3: {"pedidos": [], "auditoria_operaciones": []},
        }

    def connect_all(self):
        """Intenta conectar a cada uno de los 3 clusters de MongoDB Atlas."""
        for c_id, uri in self.uris.items():
            self.connect_cluster(c_id, uri)

    def connect_cluster(self, cluster_id: int, uri: str) -> bool:
        """Intenta inicializar la conexión con un cluster específico."""
        if settings.TESTING or ("cluster" in uri and "mongodb.net" in uri and "password123" in uri):
            self.clients[cluster_id] = None
            self.is_connected[cluster_id] = False
            self.latencies[cluster_id] = 1.0
            return True

        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=500, connectTimeoutMS=500)
            # Ping para verificar conectividad real
            start = time.time()
            client.admin.command("ping")
            self.latencies[cluster_id] = round((time.time() - start) * 1000, 2)
            self.clients[cluster_id] = client
            self.is_connected[cluster_id] = True
            logger.info(f"MongoDB Cluster #{cluster_id} conectado con éxito ({self.latencies[cluster_id]} ms).")
            return True
        except Exception as e:
            logger.warning(f"No se pudo conectar a MongoDB Cluster #{cluster_id} ({e}). Usando modo resiliente.")
            self.clients[cluster_id] = None
            self.is_connected[cluster_id] = False
            self.latencies[cluster_id] = 1.5  # Latencia mock simulada
            return False

    def get_database(self, cluster_id: int):
        """Obtiene la instancia de la base de datos para el cluster indicado."""
        if self.is_connected[cluster_id] and self.clients[cluster_id]:
            return self.clients[cluster_id][self.db_name]
        return None

    # ---------------- Operaciones CRUD ----------------

    def insert_pedido(self, cluster_id: int, pedido_doc: dict) -> dict:
        """Inserta un pedido en el cluster indicado."""
        db = self.get_database(cluster_id)
        if db is not None:
            res = db.pedidos.insert_one(pedido_doc)
            pedido_doc["_id"] = str(res.inserted_id)
        else:
            # Fallback local
            if "_id" not in pedido_doc:
                pedido_doc["_id"] = f"mock_{int(time.time() * 1000)}"
            self._mock_storage[cluster_id]["pedidos"].append(pedido_doc)

        # Registrar auditoría
        self.log_operation(cluster_id, "INSERT", pedido_doc.get("_id", "unknown"))
        return pedido_doc

    def get_pedidos(self, cluster_id: Optional[int] = None) -> List[dict]:
        """Obtiene pedidos de un cluster o de los 3 clusters combinados."""
        clusters_to_check = [cluster_id] if cluster_id in (1, 2, 3) else [1, 2, 3]
        all_pedidos = []

        for cid in clusters_to_check:
            db = self.get_database(cid)
            if db is not None:
                docs = list(db.pedidos.find())
                for d in docs:
                    d["_id"] = str(d["_id"])
                    d["_cluster_origen"] = f"Cluster Mongo #{cid}"
                all_pedidos.extend(docs)
            else:
                for d in self._mock_storage[cid]["pedidos"]:
                    item = dict(d)
                    item["_cluster_origen"] = f"Cluster Mongo #{cid}"
                    all_pedidos.append(item)

        return all_pedidos

    def get_pedido_by_id(self, cluster_id: int, pedido_id: str) -> Optional[dict]:
        """Busca un pedido por su identificador en el cluster especificado."""
        db = self.get_database(cluster_id)
        if db is not None:
            from bson.objectid import ObjectId
            try:
                doc = db.pedidos.find_one({"_id": ObjectId(pedido_id)})
            except Exception:
                doc = db.pedidos.find_one({"_id": pedido_id})
            if doc:
                doc["_id"] = str(doc["_id"])
                return doc
        else:
            for d in self._mock_storage[cluster_id]["pedidos"]:
                if str(d.get("_id")) == str(pedido_id):
                    return d
        return None

    def update_pedido(self, cluster_id: int, pedido_id: str, updates: dict) -> bool:
        """Actualiza un pedido existente."""
        updates["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        updates["sync_status"] = "PENDING"

        db = self.get_database(cluster_id)
        if db is not None:
            from bson.objectid import ObjectId
            query = {"_id": ObjectId(pedido_id)} if len(pedido_id) == 24 else {"_id": pedido_id}
            res = db.pedidos.update_one(query, {"$set": updates})
            self.log_operation(cluster_id, "UPDATE", pedido_id)
            return res.modified_count > 0
        else:
            for d in self._mock_storage[cluster_id]["pedidos"]:
                if str(d.get("_id")) == str(pedido_id):
                    d.update(updates)
                    self.log_operation(cluster_id, "UPDATE", pedido_id)
                    return True
            return False

    def delete_pedido(self, cluster_id: int, pedido_id: str) -> bool:
        """Elimina un pedido en el cluster indicado."""
        db = self.get_database(cluster_id)
        if db is not None:
            from bson.objectid import ObjectId
            query = {"_id": ObjectId(pedido_id)} if len(pedido_id) == 24 else {"_id": pedido_id}
            res = db.pedidos.delete_one(query)
            self.log_operation(cluster_id, "DELETE", pedido_id)
            return res.deleted_count > 0
        else:
            prev_len = len(self._mock_storage[cluster_id]["pedidos"])
            self._mock_storage[cluster_id]["pedidos"] = [
                d for d in self._mock_storage[cluster_id]["pedidos"]
                if str(d.get("_id")) != str(pedido_id)
            ]
            deleted = len(self._mock_storage[cluster_id]["pedidos"]) < prev_len
            if deleted:
                self.log_operation(cluster_id, "DELETE", pedido_id)
            return deleted

    def mark_pedidos_synced(self, cluster_id: int, pedido_ids: List[str]):
        """Marca una lista de pedidos como sincronizados en MongoDB."""
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        db = self.get_database(cluster_id)
        if db is not None:
            from bson.objectid import ObjectId
            for pid in pedido_ids:
                q = {"_id": ObjectId(pid)} if len(pid) == 24 else {"_id": pid}
                db.pedidos.update_one(q, {"$set": {"sync_status": "SYNCED", "synced_at": now_iso}})
        else:
            for d in self._mock_storage[cluster_id]["pedidos"]:
                if str(d.get("_id")) in pedido_ids:
                    d["sync_status"] = "SYNCED"
                    d["synced_at"] = now_iso

    def log_operation(self, cluster_id: int, operacion: str, documento_id: str):
        """Registra en la colección auditoria_operaciones."""
        log_entry = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "cluster_id": cluster_id,
            "cluster_name": f"Cluster Mongo #{cluster_id}",
            "operacion": operacion,
            "documento_id": str(documento_id)
        }
        db = self.get_database(cluster_id)
        if db is not None:
            try:
                db.auditoria_operaciones.insert_one(log_entry)
            except Exception:
                pass
        else:
            self._mock_storage[cluster_id]["auditoria_operaciones"].append(log_entry)

    def get_cluster_status(self) -> List[dict]:
        """Reporta la salud, latencia y cantidad de documentos de cada cluster."""
        status_list = []
        for cid in [1, 2, 3]:
            db = self.get_database(cid)
            if db is not None:
                doc_count = db.pedidos.count_documents({})
                is_live = True
            else:
                doc_count = len(self._mock_storage[cid]["pedidos"])
                is_live = self.is_connected[cid]

            status_list.append({
                "cluster_id": cid,
                "nombre": f"Cluster Mongo #{cid}",
                "rango_usuarios": f"{(cid-1)*3 + 1} - {cid*3}",
                "activo": is_live,
                "latencia_ms": self.latencies[cid],
                "total_documentos": doc_count,
                "modo": "Atlas Cloud" if self.is_connected[cid] else "Resiliente / Simulado"
            })
        return status_list


mongo_manager = MongoClusterManager()
