import time

from typing import Dict, Any, Union

from telebot.asyncio_handler_backends import BaseMiddleware, CancelUpdate
from telebot.types import Message, CallbackQuery
from app.core import bot, logger
from app.services import user_api


class AllInOneMiddleware(BaseMiddleware):
    __slots__ = ("rate_limit", "admin_ids", "last_requests", "update_types")

    def __init__(self, rate_limit: int = 2, admin_ids: list | None = None):
        super().__init__()
        self.rate_limit = rate_limit
        self.admin_ids = admin_ids or []
        self.last_requests: Dict[int, float] = {}
        self.update_types = ['message', 'callback_query']

    def _chat_id(self, message: Union[Message, CallbackQuery]) -> int:
        return message.chat.id if isinstance(message, Message) else message.message.chat.id

    async def pre_process(self, message: Union[Message, CallbackQuery], data: Any):
        await self._log_request(message)

        if not await self._check_rate_limit(message):
            return CancelUpdate()
        if not await self._check_admin_commands(message):
            return CancelUpdate()
        if not await self._check_user_status(message):
            return CancelUpdate()

        data['start_time'] = time.time()
        return True

    async def post_process(self, message: Union[Message, CallbackQuery], data: Any, exception: Exception = None):
        if 'start_time' in data:
            logger.info(f"Request completed in {time.time() - data['start_time']:.2f}s")

    async def _log_request(self, message: Union[Message, CallbackQuery]) -> None:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        if isinstance(message, Message):
            logger.info(f"Message from @{username} ({user_id}): {(message.text or message.caption or '[no text]')[:50]}")
        else:
            logger.info(f"Callback from @{username} ({user_id}): {message.data}")

    _CLEANUP_INTERVAL = 300
    _last_cleanup: float = 0.0

    async def _check_rate_limit(self, message: Union[Message, CallbackQuery]) -> bool:
        user_id = message.from_user.id
        current_time = time.time()

        if current_time - self.__class__._last_cleanup > self._CLEANUP_INTERVAL:
            cutoff = current_time - self.rate_limit * 10
            self.last_requests = {k: v for k, v in self.last_requests.items() if v >= cutoff}
            self.__class__._last_cleanup = current_time

        if user_id in self.last_requests and current_time - self.last_requests[user_id] < self.rate_limit:
            try:
                await bot.send_message(self._chat_id(message), "🚫 Too fast! Please wait.")
            except Exception:
                pass
            return False

        self.last_requests[user_id] = current_time
        return True

    async def _check_admin_commands(self, message: Union[Message, CallbackQuery]) -> bool:
        if not isinstance(message, Message) or not message.text:
            return True
        admin_commands = {'/admin', '/stats', '/broadcast', '/ban'}
        if message.text.split()[0].lower() in admin_commands and message.from_user.id not in self.admin_ids:
            await bot.send_message(self._chat_id(message), "❌ Admin only command.")
            return False
        return True

    async def _check_user_status(self, message: Union[Message, CallbackQuery]) -> bool:
        try:
            if await user_api.is_ban_user(message.from_user.id):
                await bot.send_message(self._chat_id(message), "🚫 You are banned.")
                return False
        except Exception as e:
            logger.error(f"User status check error: {e}")
        return True


def setup_my_middleware(admin_ids: list = None):
    bot.setup_middleware(AllInOneMiddleware(rate_limit=1, admin_ids=admin_ids))
    logger.info("Middleware setup completed")
