from __future__ import annotations
from dataclasses import dataclass
import os

@dataclass(frozen=True, slots=True)
class Settings:
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8080"))
    log_level: str = os.getenv("LOG_LEVEL", "info")

settings = Settings()