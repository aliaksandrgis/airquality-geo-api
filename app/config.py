from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    db_host: str = os.getenv("POSTGRES_HOST", "postgres")
    db_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    db_name: str = os.getenv("POSTGRES_DB", "airquality")
    db_user: str = os.getenv("POSTGRES_USER", "airuser")
    db_password: str = os.getenv("POSTGRES_PASSWORD", "airpassword")
    allowed_origins: list[str] = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "*").split(",")
    )


settings = Settings()
