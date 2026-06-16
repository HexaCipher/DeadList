"""
DeadList Configuration
Loads environment variables via Pydantic BaseSettings.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # Volatility 3
    VOLATILITY_PATH: str = "vol"
    PLUGIN_TIMEOUT_SECONDS: int = 1800

    # File storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_GB: int = 32

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/deadlist.db"

    # GeoIP
    GEOIP_API_URL: str = "http://ip-api.com/json"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Development
    MOCK_MODE: bool = False

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_GB * 1024 * 1024 * 1024

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname("./data/deadlist.db"), exist_ok=True)
