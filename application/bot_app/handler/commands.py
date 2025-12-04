from typing import Union

from telebot import types
from telebot.states.asyncio import StateContext

from ..handler import cmd
from ..handler.functions import main_menu


@cmd("start", "Restart Bot")
async def start_handler(
        msg: Union[types.Message, types.CallbackQuery],
        state: StateContext):
    try:
        return await main_menu(msg, state, send=True)
    except Exception as e:
        print(e)


