from datetime import datetime, timedelta, timezone
from typing import Union

from telebot import types
from telebot.states.asyncio import StateContext

from ..handler.decorator import cmd, cb, UltraHandler, BalanceState
from ..keyboards.inline import (
    main_menu_inl, register_driver_inl, balance_inl,
    choice_balance_inl, delete_inl, back_inl,
)
from ...core import t
from ...core.log import logger
from ...services import user_api, driver_api, order_api
from ...api.api_types import OrderTypes


# ── /start ──────────────────────────────────────────────────────────────────

@cmd("start", "Restart Bot")
async def start_handler(msg: Union[types.Message, types.CallbackQuery], state: StateContext):
    h = UltraHandler(msg, state)
    if await h.get_user() is None:
        await user_api.create_user({
            "telegram_id": msg.from_user.id,
            "full_name": msg.from_user.full_name,
            "username": msg.from_user.username,
        })
    await state.delete()
    lang = await h.lang()
    driver = await h.get_driver()
    if not driver:
        return await h.send("not_driver", reply_markup=register_driver_inl(lang))
    return await h.send("main_menu", reply_markup=main_menu_inl(lang))


# ── Balansni to'ldirish ──────────────────────────────────────────────────────

@cb("balance")
async def balance_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()
    driver = await driver_api.get_driver_by_telegram_id(call.message.chat.id)
    return await h.edit(
        "account_balance_info",
        reply_markup=balance_inl(lang),
        balance=f"{driver.amount:,}",
    )


@cb("top_up_balance")
async def top_up_balance_callback(call: types.CallbackQuery, state: StateContext, send=False):
    h = UltraHandler(call, state)
    lang = await h.lang()
    await h.set_state(BalanceState.upload)
    if send:
        await h.delete()
        return await h.send("top_up_request", reply_markup=choice_balance_inl(lang))
    return await h.edit("top_up_request", reply_markup=choice_balance_inl(lang))


# ── Yordam ───────────────────────────────────────────────────────────────────

@cb("help")
async def help_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    return await h.edit("contact_info", reply_markup=back_inl(await h.lang()))


# ── Buyurtmalarni qabul qilish ───────────────────────────────────────────────

@cb("accept_")
async def accept_order_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()
    _, order_type, order_id = call.data.split('_')
    try:
        order_info = OrderTypes.from_dict(await order_api.get_order(int(order_id)))
        text = _build_order_text(lang, order_info, order_info.creator.phone, is_travel=order_type == "travel")

        if order_info.status == "created" and order_info.driver_details is None:
            assigned = await order_api.add_new_driver(order_id, call.from_user.id)
            if assigned.get("status") == "assigned":
                loc = order_info.content_object.from_location.get("location", {})
                if loc.get("latitude") and loc.get("longitude"):
                    await h.location(loc["latitude"], loc["longitude"])
                return await h.edit(text, reply_markup=delete_inl(lang), translate=False)

        return await h.edit("order_taken_by_other", reply_markup=delete_inl(lang))
    except Exception as e:
        logger.error(f"accept_order_callback: {e}")


def _build_order_text(lang: str, order: OrderTypes, use_phone: str, is_travel: bool = False) -> str:
    try:
        price = float(order.content_object.price)
        if is_travel:
            price *= order.content_object.passenger
        formatted_price = f"{price:,.0f}"
    except (ValueError, TypeError):
        formatted_price = str(order.content_object.price)

    time_str = (
        datetime.fromisoformat(order.content_object.start_time.replace('Z', '+00:00'))
        .astimezone(timezone(timedelta(hours=5)))
        .strftime("%d.%m.%Y, %H:%M")
    )
    kwargs = dict(
        travel_id=order.id,
        from_city=order.content_object.route.from_city.get("translate", {}).get(lang),
        to_city=order.content_object.route.to_city.get("translate", {}).get(lang),
        price=formatted_price,
        phone=use_phone,
        comment=order.content_object.comment,
        time=time_str,
    )
    if is_travel:
        kwargs['gender_icon'] = "👩" if order.content_object.has_woman else "👤"
        kwargs['passenger'] = order.content_object.passenger
        kwargs['woman_note'] = t("woman_passenger_note", lang) if order.content_object.has_woman else ""

    return t("accepted_order_details" if is_travel else "accepted_order", lang, **kwargs)


# ── Navigatsiya utility ──────────────────────────────────────────────────────

@cb("back")
async def back_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    suffix = call.data.split('_')[-1]
    if suffix == "balance":
        await h.clear_state()
        return await balance_callback(call, state)
    if suffix == "top":
        await h.clear_state()
        await h.set_state(stat=BalanceState.upload)
        return await top_up_balance_callback(call, state, send=True)
    # default: asosiy menu
    lang = await h.lang()
    return await h.edit("main_menu", reply_markup=main_menu_inl(lang))


@cb("cancel")
async def cancel_callback(call: types.CallbackQuery, state: StateContext):
    await UltraHandler(call, state).delete()


@cb("delete")
async def delete_callback(call: types.CallbackQuery, state: StateContext):
    await UltraHandler(call, state).delete()
