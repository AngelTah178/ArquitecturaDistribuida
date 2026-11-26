import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from database.mongo_manager import mongo_manager
from database.postgres_manager import postgres_manager
from etl.scheduler import sync_scheduler
from simulator.bots import simulator_controller

# Routers
from modules.catalogos.router import router as catalogos_router
from modules.monitoreo.router import router as monitoreo_router
from simulator.router import router as simulator_router

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AppMain")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- EVENTO STARTUP ---
    logger.info("=== Iniciando Servidor de Arquitectura Distribuida UPQROO ===")
    
    # 1. Inicializar conexiones a clusters MongoDB
    mongo_manager.connect_all()
    
    # 2. Inicializar conexión a PostgreSQL Neon
    postgres_manager.connect()
    
    # 3. Iniciar Job Scheduler de sincronización automática (cada 3 min)
    if not settings.TESTING:
        sync_scheduler.start()
        # Iniciar por defecto con 3 bots para arrancar simulación en Cluster 1
        simulator_controller.set_bots_count(3)
    
    yield
    
    # --- EVENTO SHUTDOWN ---
    logger.info("=== Deteniendo Servidor y Servicios en Segundo Plano ===")
    simulator_controller.stop_all()
    sync_scheduler.stop()


app = FastAPI(
    title="UPQROO - Arquitectura Distribuida y Sincronizada",
    description=(
        "Proyecto Final Integrador: Arquitectura distribuida con enrutamiento dinámico "
        "hacia 3 clusters de MongoDB Atlas y sincronización periódica ETL (cada 3 min) "
        "hacia PostgreSQL en Neon Cloud."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Routers de la API
app.include_router(catalogos_router)
app.include_router(monitoreo_router)
app.include_router(simulator_router)

# -------------------------------------------------------------------------
# Montar recursos estáticos del Frontend (CSS y JS)
# -------------------------------------------------------------------------
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.exists(frontend_dir):
    css_dir = os.path.join(frontend_dir, "css")
    js_dir = os.path.join(frontend_dir, "js")
    
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")


# -------------------------------------------------------------------------
# Vistas Web (Frontend)
# -------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse, tags=["Oficina Virtual"])
@app.get("/oficina", response_class=HTMLResponse, tags=["Oficina Virtual"])
def get_office_frontend():
    """Sirve la nueva Oficina Virtual Pixel Art."""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Frontend index.html no encontrado en /frontend</h1>", status_code=404)


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def get_legacy_dashboard():
    """Sirve el dashboard métrico anterior como vista alternativa."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Dashboard template no encontrado</h1>", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)