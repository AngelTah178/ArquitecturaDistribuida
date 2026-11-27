import time
import threading
from typing import Dict, List, Tuple, Optional


class DynamicClusterRouter:

    def __init__(self, session_ttl_seconds: int = 45):
        self._lock = threading.Lock()
        self.session_ttl = session_ttl_seconds
        # user_id -> {"last_active": timestamp, "ip": str, "client_name": str}
        self._active_users: Dict[str, dict] = {}
        # Historial de operaciones por cluster
        self._operations_count = {
            "Cluster Mongo #1": 0,
            "Cluster Mongo #2": 0,
            "Cluster Mongo #3": 0
        }

    def touch_user(self, user_id: str, client_name: str = "Bot", ip: str = "127.0.0.1"):
        with self._lock:
            self._active_users[user_id] = {
                "user_id": user_id,
                "client_name": client_name,
                "ip": ip,
                "last_active": time.time(),
                "created_at": self._active_users.get(user_id, {}).get("created_at", time.time())
            }

    def remove_user(self, user_id: str):
        with self._lock:
            self._active_users.pop(user_id, None)

    def set_exact_active_users(self, count: int):
        with self._lock:
            self._active_users.clear()
            now = time.time()
            for i in range(1, count + 1):
                uid = f"bot_{i}"
                self._active_users[uid] = {
                    "user_id": uid,
                    "client_name": f"Bot {i}",
                    "ip": f"127.0.0.{i}",
                    "last_active": now,
                    "created_at": now
                }

    def cleanup_expired_sessions(self):
        now = time.time()
        with self._lock:
            expired = [
                uid for uid, data in self._active_users.items()
                if (now - data["last_active"]) > self.session_ttl
            ]
            for uid in expired:
                del self._active_users[uid]

    def get_active_users_count(self) -> int:
        self.cleanup_expired_sessions()
        with self._lock:
            return len(self._active_users)

        """Retorna la lista de usuarios activos con su detalle."""
        self.cleanup_expired_sessions()
        with self._lock:
            return list(self._active_users.values())

    def get_target_cluster(self, forced_count: Optional[int] = None) -> Tuple[int, str]:

        active_count = forced_count if forced_count is not None else self.get_active_users_count()

        if active_count <= 3:
            cluster_num = 1
            cluster_name = "Cluster Mongo #1"
        elif active_count <= 6:
            cluster_num = 2
            cluster_name = "Cluster Mongo #2"
        else:
            cluster_num = 3
            cluster_name = "Cluster Mongo #3"

        return cluster_num, cluster_name

    def record_operation(self, cluster_name: str):
        """Registra la ejecución de una operación en un cluster específico."""
        with self._lock:
            if cluster_name in self._operations_count:
                self._operations_count[cluster_name] += 1
            else:
                self._operations_count[cluster_name] = 1

    def get_operations_stats(self) -> Dict[str, int]:
        """Retorna el conteo de operaciones ejecutadas por cluster."""
        with self._lock:
            return dict(self._operations_count)


# Instancia singleton del enrutador dinámico
cluster_router = DynamicClusterRouter()
