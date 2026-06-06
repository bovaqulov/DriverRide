# application/app.py

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.log import logger
from app.database.cache import cache
from app.core.i18n import init_translations
from app.api.routes import router
from app.api.order_service import start_message_queue, stop_message_queue


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

        # Message queue ni ishga tushirish
        await start_message_queue()
        logger.info("✅ Application started successfully")

        yield

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    finally:
        # Shutdown
        logger.info("🛑 Shutting down application...")

        await stop_message_queue()

        # HTTP sessiyani yopish
        from app.services.http_client import GlobalHTTPClient
        await GlobalHTTPClient().close()

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
    settings.FRONTEND_URL,
    settings.WEBHOOK_URL
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in origins if o],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    logger.info(f"→ {request.method} {request.url.path} | IP: {ip}")
    try:
        response = await call_next(request)
        duration = (time.time() - start) * 1000
        logger.info(f"← {request.method} {request.url.path} | {response.status_code} | {duration:.1f}ms")
        return response
    except Exception as e:
        duration = (time.time() - start) * 1000
        logger.error(f"✗ {request.method} {request.url.path} | ERROR | {duration:.1f}ms | {e}")
        raise


app.include_router(router)