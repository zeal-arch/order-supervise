import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.api.routes import runs, supervisors
from apps.api.app.config import settings
from apps.api.app.db.database import create_db_tables, init_db_engines

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("order_supervisor.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Order Supervisor API Service...")
    init_db_engines()
    try:
        await create_db_tables()
    except Exception as e:
        logger.warning(f"Database table initialization notice: {e}")
    yield
    logger.info("Shutting down Order Supervisor API Service.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API and control plane for the Order Supervisor long-running AI orchestration system.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(supervisors.router, prefix="/api")
app.include_router(runs.router, prefix="/api")


@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "order-supervisor-api",
        "version": settings.VERSION,
        "temporal_host": settings.TEMPORAL_HOST,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
