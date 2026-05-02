# application/core/bot.py
from telebot import asyncio_filters
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from app.core.config import settings
from app.core.log import logger
from telebot.states.asyncio.middleware import StateMiddleware


# State storage for TeleBot
state_storage = StateMemoryStorage()

# Create bot instance
bot = AsyncTeleBot(
    token=settings.BOT_TOKEN,
    parse_mode="HTML",
    state_storage=state_storage
)

logger.info("🤖 Bot instance created")

bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.setup_middleware(StateMiddleware(bot))