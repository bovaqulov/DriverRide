from typing import Union

from telebot import types
from telebot.states.asyncio import StateContext

from ..handler import UltraHandler
from ..keyboards.inline import main_menu_inl, register_driver_inl
from ...core import t
from ...services.driver_service import DriverServiceAPI
from ...services.types import DriverService, UserService



async def main_menu(
        msg: Union[types.Message, types.CallbackQuery],
        state: StateContext,
        status: str = None,
        send: bool = False,

):
    h = UltraHandler(msg, state)
    lang = await h.lang()
    user: UserService = await h.get_user()
    driver_api = DriverServiceAPI()

    driver: Union[DriverService] = await driver_api.get_driver_by_telegram_id(msg.from_user.id)

    if not driver:
        return await h.send(
            "not_driver",
            reply_markup=register_driver_inl(lang))

    if status:
        await driver_api.update_driver(driver.id, {"status": status})
        driver_status = status
    else:
        driver_status = driver.status

    if send:
        await h.clear_state()
        func = h.send
    else:
        func = h.edit

    return await func(
        "driver_profile_status",
        reply_markup=main_menu_inl(lang, driver_status),
        balance=f"{driver.amount:,}",
        rating=user.rating,
        status=t(driver_status, lang),
        direction=f'{t(driver.from_location, lang)} -> {t(driver.to_location, lang)}'
    )


