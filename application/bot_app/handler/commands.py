from typing import Union

from telebot import types
from telebot.states.asyncio import StateContext

from . import UltraHandler
from ..handler import cmd
from ..handler.functions import main_menu
from ...services import TelegramUser


@cmd("start", "Restart Bot")
async def start_handler(
        msg: Union[types.Message, types.CallbackQuery],
        state: StateContext):
    try:

        h = UltraHandler(msg, state)
        user = await h.get_user()

        if user is None:
            obj = TelegramUser()
            await obj.create_user({
                "telegram_id": msg.from_user.id,
                "full_name": msg.from_user.full_name,
                "username": msg.from_user.username,
            })

        await state.delete()

        return await main_menu(msg, state, send=True)
    except Exception as e:
        print(e)


