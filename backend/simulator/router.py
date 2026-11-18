from fastapi import APIRouter, Query
from simulator.bots import simulator_controller

router = APIRouter(prefix="/api/v1/bots", tags=["Simulador de Bots (Capa 1)"])


@router.get("/status", summary="Estado de los Bots Concurrentes")
def get_bots_status():
    """Retorna el estado de ejecución, operaciones CRUD y cluster en uso de los 9 bots."""
    return simulator_controller.get_status()


@router.post("/control", summary="Control de Concurrencia de Bots")
def control_bots(count: int = Query(..., ge=0, le=9, description="Cantidad de bots concurrentes a activar (0 a 9)")):
    """
    Ajusta dinámicamente la cantidad de bots en ejecución:
      - 1 a 3 bots -> Cluster Mongo #1
      - 4 a 6 bots -> Cluster Mongo #2
      - 7 a 9 bots -> Cluster Mongo #3
    """
    simulator_controller.set_bots_count(count)
    return {
        "mensaje": f"Simulador configurado a {count} bots activos",
        "bots_activos": count
    }


@router.post("/stop", summary="Detener todos los bots")
def stop_bots():
    simulator_controller.stop_all()
    return {"mensaje": "Todos los bots han sido detenidos"}
