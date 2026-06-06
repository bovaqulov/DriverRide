from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import JSONResponse
from telebot.types import Update

from .order_service import OrderResponse
from ..core.bot import bot
from ..core.config import settings
from ..core.log import logger
from ..database.cache import cache
from ..core.i18n import t

router = APIRouter()


@router.get("/")
async def root():
    return {"service": "Driver Bot API", "version": "1.0.0", "status": "running"}


@router.get("/health")
async def health():
    try:
        await cache.client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=503)


@router.get("/translate/{key}")
async def translate(key: str, lang: str = "en"):
    return {"key": key, "lang": lang, "value": t(key, lang)}


@router.post("/webhook")
async def webhook(request: Request):
    if settings.WEBHOOK_SECRET:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != settings.WEBHOOK_SECRET:
            ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "?")
            logger.warning(f"[webhook] invalid secret token | IP={ip}")
            return JSONResponse({"detail": "Forbidden"}, status_code=403)
    try:
        body = await request.body()
        update_obj = Update.de_json(body.decode("utf-8"))
        update_id = getattr(update_obj, "update_id", "?")
        update_type = (
            "message" if update_obj.message
            else "callback_query" if update_obj.callback_query
            else "other"
        )
        logger.info(f"[webhook] update_id={update_id} type={update_type}")
        await bot.process_new_updates([update_obj])
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"[webhook] processing error: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/set-webhook")
async def set_webhook():
    try:
        await bot.remove_webhook()
        kwargs = {"url": f"{settings.WEBHOOK_URL}/webhook"}
        if settings.WEBHOOK_SECRET:
            kwargs["secret_token"] = settings.WEBHOOK_SECRET
        await bot.set_webhook(**kwargs)
        info = await bot.get_webhook_info()
        return JSONResponse({"status": "success", "webhook_url": info.url})
    except Exception as e:
        logger.error(f"set-webhook error: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/driver")
async def travel_started(request: Request):
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "?")
    logger.info(f"[/driver] incoming order request | IP={ip}")
    result = await OrderResponse(request).control()
    logger.info(f"[/driver] order processed")
    return result
