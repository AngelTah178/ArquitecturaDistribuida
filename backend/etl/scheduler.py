import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from etl.sync_service import etl_service
from core.config import settings

logger = logging.getLogger("ETLScheduler")


class SyncScheduler:
    """Administra el Job Scheduler de sincronización automática cada 3 minutos."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.interval_minutes = settings.SYNC_INTERVAL_MINUTES
        self.is_started = False

    def start(self):
        """Inicia el planificador de sincronización."""
        if not self.is_started:
            self.scheduler.add_job(
                func=etl_service.run_pipeline,
                trigger=IntervalTrigger(minutes=self.interval_minutes),
                id="etl_sync_job",
                name="Sincronización Periódica MongoDB -> PostgreSQL Neon",
                replace_existing=True
            )
            self.scheduler.start()
            self.is_started = True
            logger.info(f"Scheduler ETL iniciado. Ejecución configurada cada {self.interval_minutes} minutos.")

    def stop(self):
        """Detiene el planificador si está activo."""
        if self.is_started:
            self.scheduler.shutdown(wait=False)
            self.is_started = False
            logger.info("Scheduler ETL detenido.")


sync_scheduler = SyncScheduler()
