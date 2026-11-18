import pytest
from core.config import settings
settings.TESTING = True

from modules.monitoreo.router import get_health, get_clusters, get_metrics, get_sincronizacion, get_estadisticas
from modules.catalogos.router import crear_pedido, listar_pedidos, obtener_pedido, actualizar_pedido, eliminar_pedido
from modules.catalogos.schemas import PedidoCreateSchema, ClienteSchema, ItemProductoSchema, PedidoUpdateSchema
from simulator.router import get_bots_status, control_bots, stop_bots


def test_health_check_endpoint():
    data = get_health()
    assert data["status"] == "healthy"
    assert "clusters_mongodb" in data
    assert "postgresql_neon" in data
    assert len(data["clusters_mongodb"]) == 3


def test_monitoreo_clusters_endpoint():
    data = get_clusters()
    assert "regla_escalamiento" in data
    assert len(data["clusters"]) == 3
    assert data["regla_escalamiento"]["1-3_usuarios"] == "Cluster Mongo #1"
    assert data["regla_escalamiento"]["4-6_usuarios"] == "Cluster Mongo #2"
    assert data["regla_escalamiento"]["7-9_usuarios"] == "Cluster Mongo #3"


def test_monitoreo_metrics_endpoint():
    data = get_metrics()
    assert "mongodb" in data
    assert "postgresql" in data
    assert "estado_sincronizacion" in data
    assert data["postgresql"]["tablas_sincronizadas"] == 5


def test_estadisticas_endpoint():
    data = get_estadisticas()
    assert "usuarios_activos" in data
    assert "mongodb" in data
    assert "postgresql_neon" in data


def test_crud_pedido_lifecycle():
    # 1. Crear Pedido
    payload = PedidoCreateSchema(
        cliente=ClienteSchema(
            nombre="Juan Perez Alumno",
            correo="juan.perez@upqroo.edu.mx",
            telefono="9981234567"
        ),
        productos=[
            ItemProductoSchema(id=1, sku="PROD-001", nombre="Sensor IoT", cantidad=2, precio=450.0)
        ],
        fecha="2026-11-18"
    )
    res_crear = crear_pedido(pedido=payload, x_user="bot_1")
    assert res_crear["mensaje"] == "Pedido registrado exitosamente"
    assert "Cluster Mongo" in res_crear["cluster_utilizado"]
    pedido_id = str(res_crear["pedido"]["_id"])

    # 2. Consultar Pedido
    res_get = obtener_pedido(pedido_id=pedido_id)
    assert res_get["cliente"]["correo"] == "juan.perez@upqroo.edu.mx"

    # 3. Listar Pedidos
    res_lista = listar_pedidos()
    assert res_lista["total"] >= 1

    # 4. Actualizar Pedido
    res_upd = actualizar_pedido(pedido_id=pedido_id, updates=PedidoUpdateSchema(fecha="2026-11-19"))
    assert res_upd["mensaje"] == "Pedido actualizado con éxito"

    # 5. Eliminar Pedido
    res_del = eliminar_pedido(pedido_id=pedido_id)
    assert res_del["mensaje"] == "Pedido eliminado correctamente"


def test_simulator_bots_endpoints():
    res_ctrl = control_bots(count=3)
    assert res_ctrl["bots_activos"] == 3

    status_list = get_bots_status()
    assert len(status_list) == 9

    res_stop = stop_bots()
    assert "detenidos" in res_stop["mensaje"]
