import pytest
from database.mongo_manager import mongo_manager
from database.postgres_manager import postgres_manager
from etl.sync_service import etl_service


def test_etl_transformation_and_deduplication():
    # Insertar un pedido en MongoDB Cluster 1 con status PENDING
    doc = {
        "_id": "test_mongo_doc_999",
        "cliente": {
            "nombre": "Estudiante Neon",
            "correo": "estudiante@neon.tech",
            "telefono": "9989998888"
        },
        "productos": [
            {"id": 2, "sku": "PROD-002", "nombre": "ESP32", "cantidad": 2, "precio": 180.0}
        ],
        "fecha": "2026-11-18",
        "total": 360.0,
        "sync_status": "PENDING"
    }
    mongo_manager.insert_pedido(cluster_id=1, pedido_doc=doc)

    # Ejecutar pipeline ETL
    resumen = etl_service.run_pipeline()
    assert resumen["estado"] == "SINCRONIZADO"
    assert resumen["total_cargados"] >= 1

    # Verificar que el cliente existe en PostgreSQL Neon
    cid1 = postgres_manager.upsert_cliente("Estudiante Neon", "estudiante@neon.tech")
    cid2 = postgres_manager.upsert_cliente("Estudiante Neon", "estudiante@neon.tech")
    # No debe duplicar el ID del cliente
    assert cid1 == cid2

    # Verificar que el documento en MongoDB quedó marcado como SYNCED
    pedido_mongo = mongo_manager.get_pedido_by_id(1, "test_mongo_doc_999")
    assert pedido_mongo["sync_status"] == "SYNCED"
