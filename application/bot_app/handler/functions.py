from typing import Union

from telebot import types
from telebot.states.asyncio import StateContext

from ..handler import UltraHandler
from ..keyboards.inline import main_menu_inl, register_driver_inl, balance_inl
from ...core import t
from ...services.driver_service import DriverServiceAPI
from ...services.types import DriverService


async def main_menu(
        msg: Union[types.Message, types.CallbackQuery],
        state: StateContext,
        status: str = None,
        send: bool = False,

):

    h = UltraHandler(msg, state)
    lang = await h.lang()
    driver_api = DriverServiceAPI()
    driver: Union[DriverService] = await h.get_driver()

    if not driver:
        return await h.send(
            "not_driver",
            reply_markup=register_driver_inl(lang))

    if 15000 > driver.amount:
        await driver_api.update_driver(driver.id, {"status": "offline"})
        if isinstance(msg, types.Message):
            func = h.send
        else:
            func = h.edit

        return await func(
            "minimum_balance_required",
            reply_markup=balance_inl(lang, balance=False)
        )

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
        balance=f"{int(driver.amount)}",
        status=t(driver_status, lang),
        direction=f"{driver.from_location.get("translate", {})[lang]} → {driver.to_location.get("translate", {})[lang]}",
        car_model=f"{driver.cars[0].car_model}",
        tariff=f"{driver.cars[0].tariff.translate[lang]}",
    )
