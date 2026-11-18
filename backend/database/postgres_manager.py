import time
import logging
from typing import Dict, Any, List, Optional, Tuple
import psycopg

from core.config import settings

logger = logging.getLogger("PostgresManager")


class PostgresManager:
    """
    Gestiona la conexión y operaciones transaccionales sobre PostgreSQL (Neon Cloud)
    para el modelo relacional de 5 tablas:
      1. clientes
      2. productos
      3. pedidos
      4. detalle_pedido
      5. sync_logs
    Incluye fallback resiliente local para desarrollo y pruebas.
    """

    def __init__(self):
        self.uri = settings.POSTGRES_NEON_URI
        self.is_connected = False
        self.latency_ms = 0.0

        # Almacenamiento local en memoria como fallback / mock
        self._mock_tables = {
            "clientes": [],
            "productos": [
                {"producto_id": 1, "sku": "PROD-001", "nombre": "Sensor IoT de Temperatura", "precio": 450.00, "stock": 100},
                {"producto_id": 2, "sku": "PROD-002", "nombre": "Microcontrolador ESP32 WiFi/BLE", "precio": 180.00, "stock": 250},
                {"producto_id": 3, "sku": "PROD-003", "nombre": "Módulo Gateway LoRaWAN", "precio": 1250.00, "stock": 50},
                {"producto_id": 4, "sku": "PROD-004", "nombre": "Actuador Relevador 4 Canales", "precio": 120.00, "stock": 300},
                {"producto_id": 5, "sku": "PROD-005", "nombre": "Fuente de Poder 12V 5A", "precio": 320.00, "stock": 80},
            ],
            "pedidos": [],
            "detalle_pedido": [],
            "sync_logs": []
        }
        self._seq = {
            "cliente_id": 1,
            "producto_id": 6,
            "pedido_id": 1,
            "detalle_id": 1,
            "sync_id": 1
        }

    def connect(self) -> bool:
        """Prueba la conexión a PostgreSQL Neon."""
        if settings.TESTING or ("ep-cool-neon" in self.uri and "password123" in self.uri):
            self.is_connected = False
            self.latency_ms = 1.0
            return True

        try:
            start = time.time()
            with psycopg.connect(self.uri, connect_timeout=1) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    cur.fetchone()
            self.latency_ms = round((time.time() - start) * 1000, 2)
            self.is_connected = True
            logger.info(f"PostgreSQL Neon conectado exitosamente ({self.latency_ms} ms).")
            return True
        except Exception as e:
            logger.warning(f"No se pudo conectar a PostgreSQL Neon ({e}). Usando modo local resiliente.")
            self.is_connected = False
            self.latency_ms = 2.0
            return False

    def upsert_cliente(self, nombre: str, correo: str, telefono: Optional[str] = None) -> int:
        """Inserta o actualiza un cliente garantizando no duplicados."""
        if self.is_connected:
            try:
                with psycopg.connect(self.uri) as conn:
                    with conn.cursor() as cur:
                        query = """
                            INSERT INTO clientes (nombre, correo, telefono)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (correo) 
                            DO UPDATE SET nombre = EXCLUDED.nombre, telefono = COALESCE(EXCLUDED.telefono, clientes.telefono)
                            RETURNING cliente_id;
                        """
                        cur.execute(query, (nombre, correo, telefono))
                        res = cur.fetchone()
                        conn.commit()
                        return res[0]
            except Exception as e:
                logger.error(f"Error en Neon upsert_cliente: {e}")

        # Fallback local
        for c in self._mock_tables["clientes"]:
            if c["correo"] == correo:
                c["nombre"] = nombre
                if telefono:
                    c["telefono"] = telefono
                return c["cliente_id"]

        cid = self._seq["cliente_id"]
        self._seq["cliente_id"] += 1
        self._mock_tables["clientes"].append({
            "cliente_id": cid,
            "nombre": nombre,
            "correo": correo,
            "telefono": telefono,
            "creado_en": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        return cid

    def get_or_create_producto(self, nombre: str, precio: float, sku: Optional[str] = None) -> int:
        """Busca o registra un producto de catálogo."""
        if self.is_connected:
            try:
                with psycopg.connect(self.uri) as conn:
                    with conn.cursor() as cur:
                        if sku:
                            cur.execute("SELECT producto_id FROM productos WHERE sku = %s;", (sku,))
                            row = cur.fetchone()
                            if row:
                                return row[0]
                        cur.execute(
                            "INSERT INTO productos (nombre, precio, sku) VALUES (%s, %s, %s) RETURNING producto_id;",
                            (nombre, precio, sku or f"SKU-{int(time.time()*1000)}")
                        )
                        res = cur.fetchone()
                        conn.commit()
                        return res[0]
            except Exception as e:
                logger.error(f"Error en Neon get_or_create_producto: {e}")

        # Fallback local
        for p in self._mock_tables["productos"]:
            if (sku and p.get("sku") == sku) or p["nombre"].lower() == nombre.lower():
                return p["producto_id"]

        pid = self._seq["producto_id"]
        self._seq["producto_id"] += 1
        self._mock_tables["productos"].append({
            "producto_id": pid,
            "nombre": nombre,
            "precio": precio,
            "sku": sku or f"SKU-{pid}",
            "stock": 100
        })
        return pid

    def insert_pedido(self, cliente_id: int, fecha: str, mongo_id: str, cluster_origen: str, total: float) -> int:
        """Inserta o actualiza un pedido sincronizado de MongoDB."""
        if self.is_connected:
            try:
                with psycopg.connect(self.uri) as conn:
                    with conn.cursor() as cur:
                        query = """
                            INSERT INTO pedidos (cliente_id, fecha, mongo_id, cluster_origen, total, sincronizado_en)
                            VALUES (%s, %s, %s, %s, %s, NOW())
                            ON CONFLICT (mongo_id)
                            DO UPDATE SET total = EXCLUDED.total, sincronizado_en = NOW()
                            RETURNING pedido_id;
                        """
                        cur.execute(query, (cliente_id, fecha, mongo_id, cluster_origen, total))
                        res = cur.fetchone()
                        conn.commit()
                        return res[0]
            except Exception as e:
                logger.error(f"Error en Neon insert_pedido: {e}")

        # Fallback local
        for p in self._mock_tables["pedidos"]:
            if p.get("mongo_id") == mongo_id:
                p["total"] = total
                p["sincronizado_en"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                return p["pedido_id"]

        pid = self._seq["pedido_id"]
        self._seq["pedido_id"] += 1
        self._mock_tables["pedidos"].append({
            "pedido_id": pid,
            "cliente_id": cliente_id,
            "fecha": fecha,
            "mongo_id": mongo_id,
            "cluster_origen": cluster_origen,
            "total": total,
            "sincronizado_en": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        })
        return pid

    def insert_detalle_pedido(self, pedido_id: int, producto_id: int, cantidad: int, precio_unitario: float) -> int:
        """Inserta detalle de pedido."""
        if self.is_connected:
            try:
                with psycopg.connect(self.uri) as conn:
                    with conn.cursor() as cur:
                        query = """
                            INSERT INTO detalle_pedido (pedido_id, producto_id, cantidad, precio_unitario)
                            VALUES (%s, %s, %s, %s)
                            RETURNING detalle_id;
                        """
                        cur.execute(query, (pedido_id, producto_id, cantidad, precio_unitario))
                        res = cur.fetchone()
                        conn.commit()
                        return res[0]
            except Exception as e:
                logger.error(f"Error en Neon insert_detalle_pedido: {e}")

        did = self._seq["detalle_id"]
        self._seq["detalle_id"] += 1
        self._mock_tables["detalle_pedido"].append({
            "detalle_id": did,
            "pedido_id": pedido_id,
            "producto_id": producto_id,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "subtotal": round(cantidad * precio_unitario, 2)
        })
        return did

    def insert_sync_log(self, cluster_origen: str, extraidos: int, cargados: int, estado: str, tiempo_ms: int, mensaje: str = ""):
        """Registra la auditoría del proceso ETL en la tabla sync_logs."""
        if self.is_connected:
            try:
                with psycopg.connect(self.uri) as conn:
                    with conn.cursor() as cur:
                        query = """
                            INSERT INTO sync_logs (cluster_origen, registros_extraidos, registros_cargados, estado, tiempo_ms, mensaje)
                            VALUES (%s, %s, %s, %s, %s, %s);
                        """
                        cur.execute(query, (cluster_origen, extraidos, cargados, estado, tiempo_ms, mensaje))
                        conn.commit()
                        return
            except Exception as e:
                logger.error(f"Error en Neon insert_sync_log: {e}")

        sid = self._seq["sync_id"]
        self._seq["sync_id"] += 1
        self._mock_tables["sync_logs"].append({
            "sync_id": sid,
            "fecha_ejecucion": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "cluster_origen": cluster_origen,
            "registros_extraidos": extraidos,
            "registros_cargados": cargados,
            "estado": estado,
            "tiempo_ms": tiempo_ms,
            "mensaje": mensaje
        })

    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de PostgreSQL para las tarjetas del Dashboard."""
        if self.is_connected:
            try:
                with psycopg.connect(self.uri) as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM clientes;")
                        total_clientes = cur.fetchone()[0]
                        cur.execute("SELECT COUNT(*) FROM pedidos;")
                        total_pedidos = cur.fetchone()[0]
                        cur.execute("SELECT COUNT(*) FROM detalle_pedido;")
                        total_detalles = cur.fetchone()[0]
                        cur.execute("SELECT COUNT(*) FROM productos;")
                        total_productos = cur.fetchone()[0]
                        cur.execute("SELECT estado, fecha_ejecucion FROM sync_logs ORDER BY fecha_ejecucion DESC LIMIT 1;")
                        last_sync = cur.fetchone()
                        return {
                            "registros_totales": total_clientes + total_pedidos + total_detalles + total_productos,
                            "tablas_sincronizadas": 5,
                            "total_pedidos": total_pedidos,
                            "total_clientes": total_clientes,
                            "errores_carga": 0,
                            "ultima_sincronizacion": last_sync[1].strftime("%Y-%m-%d %H:%M:%S") if last_sync else "Sin registros",
                            "estado_ultimo_sync": last_sync[0] if last_sync else "SINCRONIZADO",
                            "modo": "Neon Cloud"
                        }
            except Exception as e:
                logger.error(f"Error obteniendo métricas de Neon: {e}")

        # Fallback local
        total_reg = (
            len(self._mock_tables["clientes"]) +
            len(self._mock_tables["productos"]) +
            len(self._mock_tables["pedidos"]) +
            len(self._mock_tables["detalle_pedido"])
        )
        last_log = self._mock_tables["sync_logs"][-1] if self._mock_tables["sync_logs"] else None
        return {
            "registros_totales": total_reg,
            "tablas_sincronizadas": 5,
            "total_pedidos": len(self._mock_tables["pedidos"]),
            "total_clientes": len(self._mock_tables["clientes"]),
            "errores_carga": 0,
            "ultima_sincronizacion": last_log["fecha_ejecucion"] if last_log else "Pendiente",
            "estado_ultimo_sync": last_log["estado"] if last_log else "SINCRONIZADO",
            "modo": "Resiliente / Simulado"
        }


postgres_manager = PostgresManager()
