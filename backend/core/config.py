import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Arquitectura Distribuida UPQROO"
    APP_ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # MongoDB Atlas Clusters
    MONGO_CLUSTER_1_URI: str = "mongodb://localhost:27017/cluster1"
    MONGO_CLUSTER_2_URI: str = "mongodb://localhost:27017/cluster2"
    MONGO_CLUSTER_3_URI: str = "mongodb://localhost:27017/cluster3"
    MONGO_DB_NAME: str = "upqroo_distribuida"

    # PostgreSQL (Neon Cloud)
    POSTGRES_NEON_URI: str = "postgresql://dev1:password123@localhost:5432/upqroo_distribuida"

    # Scheduler ETL
    SYNC_INTERVAL_MINUTES: int = 3

    # Fallback / Mock
    ENABLE_MOCK_FALLBACK: bool = True
    TESTING: bool = False

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
