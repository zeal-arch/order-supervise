import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    PROJECT_NAME: str = "Order Supervisor API"
    VERSION: str = "1.0.0"
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/order_supervisor"
    )
    USE_SQLITE_FALLBACK: bool = True
    SQLITE_URL: str = "sqlite+aiosqlite:///./order_supervisor.db"

    # Temporal
    TEMPORAL_HOST: str = os.getenv("TEMPORAL_HOST", "localhost:7233")
    TEMPORAL_NAMESPACE: str = os.getenv("TEMPORAL_NAMESPACE", "default")
    TEMPORAL_TASK_QUEUE: str = os.getenv("TEMPORAL_TASK_QUEUE", "order-supervisor-task-queue")

    # LLM
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # CORS
    CORS_ORIGINS: list[str] = field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    )


settings = Settings()
