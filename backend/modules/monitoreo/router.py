import time
from typing import Optional
from fastapi import APIRouter, status
from common.cluster_router import cluster_router
from database.mongo_manager import mongo_manager
from database.postgres_manager import postgres_manager
from etl.sync_service import etl_service

router = APIRouter(tags=["Consultas y Monitoreo"])


# ==========================================
# SECCIÓN: CONSULTAS (Página 2 de la Rúbrica)
# ==========================================

@router.get("/estadisticas", summary="Estadísticas Generales")
def get_estadisticas():
    """
    Retorna métricas cuantitativas del sistema distribuido:
    total de documentos en Mongo, registros en Postgres y operaciones por cluster.
    """
    mongo_status = mongo_manager.get_cluster_status()
    total_mongo_docs = sum(c["total_documentos"] for c in mongo_status)
    postgres_stats = postgres_manager.get_metrics()
    op_stats = cluster_router.get_operations_stats()
    active_count = cluster_router.get_active_users_count()
    current_cluster_id, current_cluster_name = cluster_router.get_target_cluster()

    return {
        "usuarios_activos": active_count,
        "cluster_actual_enrutado": current_cluster_name,
        "mongodb": {
            "total_documentos": total_mongo_docs,
            "clusters": mongo_status
        },
        "postgresql_neon": postgres_stats,
        "operaciones_por_cluster": op_stats
    }


@router.get("/sincronizacion", summary="Estado del Servicio ETL de Sincronización")
def get_sincronizacion():
    """Retorna el estado del proceso de sincronización automática (cada 3 min) entre MongoDB y PostgreSQL Neon."""
    return etl_service.get_status()


@router.post("/sincronizacion/trigger", summary="Disparar Sincronización Manual")
def trigger_sincronizacion():
    """Permite forzar la ejecución del pipeline ETL inmediatamente para pruebas o demostraciones."""
    resumen = etl_service.run_pipeline()
    return {
        "mensaje": "Pipeline de sincronización ejecutado",
        "resumen": resumen
    }


@router.get("/health", summary="Health Check del Sistema Distribuido")
def get_health():
    """Verifica el estado de salud y conectividad de los 3 Clusters Mongo y PostgreSQL Neon."""
    clusters_info = mongo_manager.get_cluster_status()
    postgres_metrics = postgres_manager.get_metrics()

    return {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "clusters_mongodb": clusters_info,
        "postgresql_neon": {
            "conectado": postgres_manager.is_connected,
            "latencia_ms": postgres_manager.latency_ms,
            "modo": postgres_metrics["modo"]
        }
    }


# ==========================================
# SECCIÓN: MONITOREO (Página 3 de la Rúbrica)
# ==========================================

@router.get("/clusters", summary="Monitoreo de Clusters MongoDB")
def get_clusters():
    """Retorna la lista de clusters activos, latencias y reglas de balanceo dinámico."""
    return {
        "regla_escalamiento": {
            "1-3_usuarios": "Cluster Mongo #1",
            "4-6_usuarios": "Cluster Mongo #2",
            "7-9_usuarios": "Cluster Mongo #3"
        },
        "cluster_activo_actual": cluster_router.get_target_cluster()[1],
        "clusters": mongo_manager.get_cluster_status()
    }


@router.get("/usuarios", summary="Monitoreo de Usuarios/Bots Activos")
def get_usuarios():
    """Lista los usuarios y bots activos concurrentes conectados al sistema."""
    usuarios = cluster_router.get_active_users()
    active_count = len(usuarios)
    target_cluster_id, target_cluster_name = cluster_router.get_target_cluster(active_count)

    return {
        "total_activos": active_count,
        "cluster_asignado": target_cluster_name,
        "usuarios": usuarios
    }


@router.get("/metrics", summary="Métricas de Desempeño y Carga")
def get_metrics():
    """
    Retorna métricas para tarjetas de monitoreo:
    documentos totales, sincronizados, clusters activos y tablas sincronizadas.
    """
    mongo_status = mongo_manager.get_cluster_status()
    total_mongo_docs = sum(c["total_documentos"] for c in mongo_status)
    pg_metrics = postgres_manager.get_metrics()
    etl_status = etl_service.get_status()

    return {
        "mongodb": {
            "documentos_totales": total_mongo_docs,
            "documentos_sincronizados": etl_status["total_cargados_acumulado"],
            "clusters_activos": len([c for c in mongo_status if c["activo"] or c["modo"] != ""]),
            "usuarios_conectados": cluster_router.get_active_users_count()
        },
        "postgresql": {
            "registros_totales": pg_metrics["registros_totales"],
            "tablas_sincronizadas": pg_metrics["tablas_sincronizadas"],
            "errores_carga": pg_metrics["errores_carga"],
            "ultima_sincronizacion": pg_metrics["ultima_sincronizacion"]
        },
        "estado_sincronizacion": etl_status["estado"]  # 'SINCRONIZADO', 'EN_EJECUCION', 'ERROR'
    }
