import re
import time
from functools import wraps, lru_cache
import asyncio
from typing import Any, Optional, Union, Callable, List, Dict

from telebot.states import State, StatesGroup
from telebot.states.asyncio import StateContext
from telebot.types import (
    BotCommand, CallbackQuery, InlineKeyboardMarkup, LabeledPrice, Message,
    ReplyKeyboardMarkup,
)

from ...core.bot import bot
from ...core.config import settings
from ...core.i18n import t
from ...core.log import logger
from ...services import user_api, driver_api
from ...services.user_service import UserModel

ADMINS: List[int] = []


def async_lru_cache(maxsize: int = 128):
    """Async-compatible LRU cache decorator."""
    def decorator(func):
        cache: Dict[Any, Any] = {}
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            if key not in cache:
                if len(cache) >= maxsize:
                    cache.pop(next(iter(cache)))
                cache[key] = await func(*args, **kwargs)
            return cache[key]
        wrapper.cache_clear = lambda: cache.clear()
        return wrapper
    return decorator



# ==================== STATE CLASSES ====================

class BotStates(StatesGroup):
    from_location: State = State()
    to_location: State = State()
    details: State = State()


class BalanceState(StatesGroup):
    upload: State = State()


class BotNumber(StatesGroup):
    contact: State = State()
    confirm_code: State = State()


# ==================== DECORATORS ====================

def throttle(seconds: int = 1):
    last_called = {}

    def decorator(func):
        @wraps(func)
        async def wrapper(msg: Union[Message, CallbackQuery], *args, **kwargs):
            user_id = msg.from_user.id
            now = time.time()
            if user_id in last_called and now - last_called[user_id] < seconds:
                return None
            last_called[user_id] = now
            return await func(msg, *args, **kwargs)
        return wrapper
    return decorator


def error_handler(send_to_user: bool = True):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                if send_to_user and args:
                    msg = args[0]
                    if isinstance(msg, (Message, CallbackQuery)):
                        await UltraHandler(msg).send("errors.something_went_wrong")
                return None
        return wrapper
    return decorator


# ==================== ULTRA HANDLER ====================

class UltraHandler:
    __slots__ = ('msg', 'context', '_user_cache', '_lang_cache', 'chat_id', 'user_id')

    def __init__(self, message: Union[Message, CallbackQuery], context: Optional[StateContext] = None):
        self.msg = message
        self.context = context
        self._user_cache: Optional[UserModel] = None
        self._lang_cache: Optional[str] = None
        self.user_id = message.from_user.id
        self.chat_id = (message.chat.id if isinstance(message, Message)
                        else message.message.chat.id)

    async def get_user(self) -> Optional[UserModel]:
        if not self._user_cache:
            self._user_cache = await user_api.get_user(self.user_id)
        return self._user_cache

    async def get_driver(self):
        try:
            return await driver_api.get_driver_by_telegram_id(self.user_id)
        except Exception as e:
            logger.error(f"get_driver({self.user_id}): {e}")
            return None

    async def lang(self) -> str:
        if not self._lang_cache:
            user = await self.get_user()
            self._lang_cache = user.language if user else "en"
        return self._lang_cache

    async def _(self, key: str, **kwargs) -> str:
        return t(key, await self.lang(), **kwargs)

    @error_handler(send_to_user=False)
    async def send(self, text: str, translate: bool = True,
                   reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None,
                   **kwargs) -> Optional[Message]:
        final_text = await self._(text, **kwargs) if translate else text
        try:
            return await bot.send_message(self.chat_id, final_text,
                                          reply_markup=reply_markup, parse_mode="MarkdownV2")
        except Exception as e:
            logger.warning(e)
            return await bot.send_message(self.chat_id, final_text, reply_markup=reply_markup)

    @error_handler(send_to_user=False)
    async def edit(self, text: str, translate: bool = True,
                   reply_markup: Optional[InlineKeyboardMarkup] = None,
                   **kwargs) -> Optional[Message]:
        final_text = await self._(text, **kwargs) if translate else text
        message_id = self._get_message_id()
        try:
            return await bot.edit_message_text(final_text, self.chat_id, message_id,
                                               reply_markup=reply_markup, parse_mode="MarkdownV2")
        except Exception:
            try:
                return await bot.edit_message_text(final_text, self.chat_id, message_id,
                                                   reply_markup=reply_markup)
            except Exception as e:
                logger.error(f"Error editing message: {e}")
                return None

    @error_handler(send_to_user=False)
    async def reply(self, text: str, translate: bool = True,
                    reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None,
                    **kwargs) -> Optional[Message]:
        final_text = await self._(text, **kwargs) if translate else text
        return await bot.reply_to(self.msg, final_text, reply_markup=reply_markup)

    @error_handler(send_to_user=False)
    async def location(self, latitude, longitude):
        return await bot.send_location(self.chat_id, latitude=latitude, longitude=longitude)

    @error_handler(send_to_user=False)
    async def invoice(self, text: str, description: str, prices: int, payload: str,
                      reply_markup=None):
        return await bot.send_invoice(
            self.chat_id,
            await self._(text),
            await self._(description),
            payload,
            currency="UZS",
            prices=[LabeledPrice("Driver invoice", prices)],
            provider_token=settings.BOT_PAYMENT_TOKEN,
            reply_markup=reply_markup,
        )

    @error_handler(send_to_user=False)
    async def delete(self, count: int = 1) -> bool:
        message_id = self._get_message_id()
        return await bot.delete_messages(
            self.chat_id, list(range(message_id, message_id - count, -1))
        )

    @error_handler(send_to_user=False)
    async def answer(self, text: str = "", show_alert: bool = False,
                     translate: bool = True) -> bool:
        if not isinstance(self.msg, CallbackQuery):
            return False
        final_text = await self._(text) if (text and translate) else text
        return await bot.answer_callback_query(self.msg.id, text=final_text, show_alert=show_alert)

    def _get_message_id(self) -> int:
        return (self.msg.message_id if isinstance(self.msg, Message)
                else self.msg.message.message_id)

    async def set_state(self, stat: State, data: Union[Dict[str, Any], None] = None) -> None:
        await self.context.set(stat)
        if data:
            await self.context.add_data(**data)

    async def get_state(self) -> Optional[str]:
        return await self.context.get()

    async def get_data(self) -> Dict[str, Any]:
        async with self.context.data() as data:
            return data

    async def clear_state(self) -> None:
        await self.context.delete()

    @staticmethod
    @lru_cache(maxsize=512)
    def parse_callback(data: str, sep: str = ':') -> Dict[str, str]:
        parts = data.split(sep, 3)
        return {
            'action': parts[0] if len(parts) > 0 else '',
            'value': parts[1] if len(parts) > 1 else '',
            'param': parts[2] if len(parts) > 2 else '',
            'extra': parts[3] if len(parts) > 3 else '',
            'raw': data,
        }

    @property
    def callback_data(self) -> Dict[str, str]:
        return self.parse_callback(self.msg.data) if isinstance(self.msg, CallbackQuery) else {}

    @property
    def text(self) -> str:
        if isinstance(self.msg, Message):
            return self.msg.text or self.msg.caption or ""
        return ""

    @property
    def is_callback(self) -> bool:
        return isinstance(self.msg, CallbackQuery)

    @property
    def is_message(self) -> bool:
        return isinstance(self.msg, Message)


# ==================== HANDLER MASTER ====================

class HandlerMaster:
    _commands: Dict[str, Dict] = {}
    _callbacks: Dict[str, Callable] = {}
    _messages: Dict[str, Dict] = {}
    _states: Dict[State, Callable] = {}
    _error_handlers: List[Callable] = []

    @classmethod
    def command(cls, name: str, desc: str = "", admin: bool = False, state: State = None):
        def decorator(func):
            cls._commands[name] = {'func': func, 'desc': desc, 'admin': admin, 'state': state}
            return func
        return decorator

    @classmethod
    def callback(cls, pattern: str = "", state: State = None):
        def decorator(func):
            key = f"{pattern}:{state}" if state else pattern
            cls._callbacks[key] = {'func': func, 'pattern': pattern, 'state': state}
            return func
        return decorator

    @classmethod
    def message(cls, content_types: List[str] = None, regex: str = None, state: State = None):
        def decorator(func):
            cls._messages[func.__name__] = {
                'func': func,
                'content_types': content_types or ['text'],
                'regex': regex,
                'state': state,
            }
            return func
        return decorator

    @classmethod
    def state_handler(cls, state: State):
        def decorator(func):
            cls._states[state] = func
            return func
        return decorator

    @classmethod
    def error(cls, func: Callable):
        cls._error_handlers.append(func)
        return func

    @staticmethod
    async def is_admin(user_id: int) -> bool:
        return user_id in ADMINS

    @classmethod
    async def handle_error(cls, msg: Union[Message, CallbackQuery], error: Exception):
        for handler in cls._error_handlers:
            try:
                await handler(msg, error)
            except Exception as e:
                logger.error(f"Error handler failed: {e}")

    @classmethod
    async def register_all(cls):
        await cls._register_bot_commands()

        for cmd_name, config in cls._commands.items():
            @bot.message_handler(commands=[cmd_name], state=config['state'])
            @throttle(seconds=0)
            @error_handler()
            async def cmd_handler(message: Message, state: StateContext, cfg=config):
                if cfg['admin'] and not await cls.is_admin(message.from_user.id):
                    await UltraHandler(message).send("errors.admin_only")
                    return
                await cfg['func'](message, state)

        for key, config in cls._callbacks.items():
            pattern = config['pattern']

            @bot.callback_query_handler(
                func=lambda c, p=pattern: c.data.startswith(p) if p else True,
                state=config['state'],
            )
            @error_handler()
            @throttle(seconds=1)
            async def cb_handler(call: CallbackQuery, state: StateContext, cfg=config):
                await cfg['func'](call, state)

        for state, func in cls._states.items():
            @bot.message_handler(content_types=["location", "text"], state=state)
            @bot.callback_query_handler(func=lambda call: call.data, state=state)
            @error_handler()
            async def state_msg_handler(message: Message, state: StateContext, f=func):
                await f(message, state)

        for name, config in cls._messages.items():
            @bot.message_handler(content_types=config['content_types'], state=config['state'])
            @error_handler()
            async def msg_handler(message: Message, state: StateContext, cfg=config):
                if cfg['regex'] and message.text:
                    if not re.match(cfg['regex'], message.text):
                        return
                await cfg['func'](message, state)

        logger.info(
            f"Registered: {len(cls._commands)} commands, "
            f"{len(cls._callbacks)} callbacks, "
            f"{len(cls._states)} states, "
            f"{len(cls._messages)} messages"
        )

    @classmethod
    async def _register_bot_commands(cls):
        try:
            commands_list = [
                BotCommand(command=name, description=cfg['desc'])
                for name, cfg in cls._commands.items()
                if not cfg['admin'] and cfg.get('desc')
            ]
            if commands_list:
                await bot.set_my_commands(commands_list)
                logger.info(f"Registered {len(commands_list)} bot commands")
            else:
                logger.warning("No commands to register")
        except Exception as e:
            logger.error(f"Failed to register bot commands: {e}")


# ==================== SHORTHAND ALIASES ====================

cmd = HandlerMaster.command
cb = HandlerMaster.callback
msg = HandlerMaster.message
state = HandlerMaster.state_handler
err = HandlerMaster.error
