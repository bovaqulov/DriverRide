# application/app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.log import logger
from app.database.cache import cache
from app.core.i18n import init_translations
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting application...")

    try:
        # Connect to Redis
        await cache.connect()

        # Initialize translations
        await init_translations(cache.client)

        # Setup bot handlers
        from app.bot_app.handler import setup_handlers
        await setup_handlers()
        logger.info("✅ Application started successfully")

        yield

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    finally:
        # Shutdown
        logger.info("🛑 Shutting down application...")

        # Disconnect Redis
        await cache.disconnect()

        logger.info("✅ Application stopped")


# Create FastAPI app
app = FastAPI(
    title="Driver Bot API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)
origins = [
    "http://localhost:8080",
    "http://localhost:8000",
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)