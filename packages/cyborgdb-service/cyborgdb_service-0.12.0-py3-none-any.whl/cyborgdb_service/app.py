from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from cyborgdb_service.core.config import settings
from cyborgdb_service.api.routes.health import router as health_router
from cyborgdb_service.api.routes.indexes import router as indexes_router
from cyborgdb_service.api.routes.vectors import router as vectors_router
from cyborgdb_service.db.client import initialize_client
from cyborgdb_service.core.training_manager import get_training_manager, shutdown_training_manager

logger = logging.getLogger(__name__)

# Define the lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    logger.info("Starting up CyborgDB Service...")
    initialize_client()
    
    # Initialize the training manager
    training_manager = get_training_manager()
    logger.info("Training manager initialized")
    
    # Start periodic cleanup task for stale locks
    import asyncio
    
    async def periodic_lock_cleanup():
        """Periodically clean up stale training locks."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                training_manager._training_lock.cleanup_stale_locks(max_age_seconds=1800)  # 30 min timeout
            except Exception as e:
                logger.error(f"Error during periodic lock cleanup: {e}")
    
    cleanup_task = asyncio.create_task(periodic_lock_cleanup())
    
    yield  # Application runs here
    
    # Cleanup code
    logger.info("Shutting down CyborgDB Service...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    shutdown_training_manager()
    logger.info("Training manager shutdown complete")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan  # Use the new lifespan handler
)

# Include routers
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(indexes_router, prefix=settings.API_PREFIX)
app.include_router(vectors_router, prefix=settings.API_PREFIX)