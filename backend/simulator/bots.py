import asyncio
import random
import time
import logging
from typing import Dict, List, Optional
from common.cluster_router import cluster_router
from modules.catalogos.schemas import PedidoCreateSchema, ClienteSchema, ItemProductoSchema
from modules.catalogos.service import catalogo_service

logger = logging.getLogger("BotSimulator")


SAMPLE_CLIENTES = [
    {"nombre": "Carlos Santana", "correo": "carlos.santana@mail.com", "tel": "9981122334"},
    {"nombre": "Ana Morales", "correo": "ana.morales@mail.com", "tel": "9982233445"},
    {"nombre": "Luis Ramirez", "correo": "luis.ramirez@mail.com", "tel": "9983344556"},
    {"nombre": "Sofia Mendoza", "correo": "sofia.mendoza@mail.com", "tel": "9984455667"},
    {"nombre": "Jorge Hernandez", "correo": "jorge.hernandez@mail.com", "tel": "9985566778"},
    {"nombre": "Elena Gomez", "correo": "elena.gomez@mail.com", "tel": "9986677889"},
    {"nombre": "David Castillo", "correo": "david.castillo@mail.com", "tel": "9987788990"},
    {"nombre": "Valeria Vargas", "correo": "valeria.vargas@mail.com", "tel": "9988899001"},
    {"nombre": "Fernando Rios", "correo": "fernando.rios@mail.com", "tel": "9989900112"},
]

SAMPLE_PRODUCTOS = [
    {"id": 1, "sku": "PROD-001", "nombre": "Sensor IoT de Temperatura", "precio": 450.0},
    {"id": 2, "sku": "PROD-002", "nombre": "Microcontrolador ESP32 WiFi/BLE", "precio": 180.0},
    {"id": 3, "sku": "PROD-003", "nombre": "Módulo Gateway LoRaWAN", "precio": 1250.0},
    {"id": 4, "sku": "PROD-004", "nombre": "Actuador Relevador 4 Canales", "precio": 120.0},
    {"id": 5, "sku": "PROD-005", "nombre": "Fuente de Poder 12V 5A", "precio": 320.0},
]


class BotWorker:

    def __init__(self, bot_id: int):
        self.bot_id = bot_id
        self.user_id = f"bot_{bot_id}"
        self.name = f"Bot {bot_id}"
        self.current_op = "IDLE"
        self.cluster_used = "Inactivo"
        self.ops_count = 0
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.last_status_message = "Listo para iniciar"

    async def run(self):
        self.is_running = True
        logger.info(f"{self.name} iniciado.")
        while self.is_running:
            try:
                cluster_router.touch_user(self.user_id, client_name=self.name)
                target_num, target_name = cluster_router.get_target_cluster()
                self.cluster_used = target_name

                op = random.choice(["INSERT", "INSERT", "READ", "READ", "UPDATE", "DELETE"])
                self.current_op = op

                if op == "INSERT":
                    cli = random.choice(SAMPLE_CLIENTES)
                    prod = random.sample(SAMPLE_PRODUCTOS, k=random.randint(1, 3))
                    schema = PedidoCreateSchema(
                        cliente=ClienteSchema(nombre=cli["nombre"], correo=cli["correo"], telefono=cli["tel"]),
                        productos=[ItemProductoSchema(id=p["id"], sku=p["sku"], nombre=p["nombre"], cantidad=random.randint(1, 4), precio=p["precio"]) for p in prod],
                        fecha=time.strftime("%Y-%m-%d")
                    )
                    doc, cluster = catalogo_service.crear_pedido(schema, user_id=self.user_id)
                    self.last_status_message = f"INSERT pedido {doc.get('_id')} en {cluster}"

                elif op == "READ":
                    pedidos = catalogo_service.listar_pedidos(cluster_id=target_num)
                    self.last_status_message = f"READ {len(pedidos)} pedidos desde {target_name}"

                elif op == "UPDATE":
                    pedidos = catalogo_service.listar_pedidos(cluster_id=target_num)
                    if pedidos:
                        p = random.choice(pedidos)
                        from modules.catalogos.schemas import PedidoUpdateSchema
                        catalogo_service.actualizar_pedido(str(p["_id"]), PedidoUpdateSchema(fecha=time.strftime("%Y-%m-%d")), cluster_id=target_num)
                        self.last_status_message = f"UPDATE pedido {p['_id']} en {target_name}"
                    else:
                        self.last_status_message = f"READ sin registros en {target_name}"

                elif op == "DELETE":
                    pedidos = catalogo_service.listar_pedidos(cluster_id=target_num)
                    if len(pedidos) > 10:  # Evitar vaciar la base completamente
                        p = random.choice(pedidos)
                        catalogo_service.eliminar_pedido(str(p["_id"]), cluster_id=target_num)
                        self.last_status_message = f"DELETE pedido {p['_id']} de {target_name}"
                    else:
                        self.last_status_message = f"READ conservando registros en {target_name}"

                self.ops_count += 1

                await asyncio.sleep(random.uniform(1.5, 3.5))

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.last_status_message = f"Error: {e}"
                await asyncio.sleep(2)

        self.current_op = "IDLE"
        self.is_running = False
        self._task = None
        cluster_router.remove_user(self.user_id)
        logger.info(f"{self.name} detenido.")

    def stop(self):
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None
        self.current_op = "IDLE"
        cluster_router.remove_user(self.user_id)

    def to_dict(self) -> dict:
        return {
            "bot_id": self.bot_id,
            "name": self.name,
            "user_id": self.user_id,
            "current_op": self.current_op,
            "cluster_used": self.cluster_used,
            "ops_count": self.ops_count,
            "is_running": self.is_running,
            "status_message": self.last_status_message
        }


class SimulatorController:

    def __init__(self):
        self.bots: Dict[int, BotWorker] = {i: BotWorker(i) for i in range(1, 10)}
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def set_bots_count(self, count: int):
        """Ajusta dinámicamente la cantidad de bots concurrentes activos (0 a 9)."""
        count = max(0, min(9, count))
        
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = self._loop

        for i in range(1, 10):
            bot = self.bots[i]
            if i <= count:
                if not bot.is_running or (bot._task is not None and bot._task.done()):
                    bot.is_running = True
                    if loop and loop.is_running():
                        try:
                            running = asyncio.get_running_loop()
                            bot._task = running.create_task(bot.run())
                        except RuntimeError:
                            bot._task = asyncio.run_coroutine_threadsafe(bot.run(), loop)
            else:
                if bot.is_running:
                    bot.stop()

    def stop_all(self):
        for bot in self.bots.values():
            bot.stop()

    def get_status(self) -> List[dict]:
        return [b.to_dict() for b in self.bots.values()]

    def get_active_count(self) -> int:
        return sum(1 for b in self.bots.values() if b.is_running)


simulator_controller = SimulatorController()
