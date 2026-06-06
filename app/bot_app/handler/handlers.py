from datetime import datetime, timedelta, timezone
from typing import Union

from telebot import types
from telebot.states.asyncio import StateContext

from ..handler.decorator import cmd, cb, UltraHandler, BalanceState
from ..keyboards.inline import (
    profile_inl, register_driver_inl, help_inl,
    choice_balance_inl, delete_inl, back_inl,
)
from ...core import t
from ...core.bot import bot
from ...core.log import logger
from ...services import user_api, driver_api, order_api
from ...api.api_types import OrderTypes


# ── Profil ko'rsatish uchun umumiy helper ─────────────────────────────────────

async def _render_profile(h: UltraHandler, send: bool = False):
    lang = await h.lang()
    driver = await driver_api.get_driver_by_telegram_id(h.user_id)

    if not driver:
        if send:
            return await h.send("not_driver", reply_markup=register_driver_inl(lang))
        return await h.edit("not_driver", reply_markup=register_driver_inl(lang))

    from_name = (
        driver.from_location.get("translate", {}).get(lang)
        or driver.from_location.get("title", "?")
    )
    to_name = (
        driver.to_location.get("translate", {}).get(lang)
        or driver.to_location.get("title", "?")
    )
    direction = f"{from_name} → {to_name}" if from_name and to_name else "-"

    car = driver.cars[0] if driver.cars else None
    car_model = car.car_model if car else "-"
    tariff = (
        (car.tariff.translate or {}).get(lang) or (car.tariff.title or "-")
        if car and car.tariff else "-"
    )

    text = t(
        "driver_profile_status", lang,
        status=t(driver.status, lang),
        balance=f"{driver.amount:,}",
        direction=direction,
        car_model=car_model,
        tariff=tariff,
    )
    markup = profile_inl(lang, driver.status)

    try:
        if send:
            return await bot.send_message(h.chat_id, text, reply_markup=markup, parse_mode="HTML")
        msg_id = h._get_message_id()
        return await bot.edit_message_text(text, h.chat_id, msg_id, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        logger.error(f"_render_profile send error: {e}")


# ── /start ──────────────────────────────────────────────────────────────────

@cmd("start", "Restart Bot")
async def start_handler(msg: Union[types.Message, types.CallbackQuery], state: StateContext):
    try:
        h = UltraHandler(msg, state)
        user_tag = f"@{msg.from_user.username}" if msg.from_user.username else f"id={msg.from_user.id}"
        logger.info(f"[/start] {user_tag}")
        if await h.get_user() is None:
            lang_code = (msg.from_user.language_code or "uz").split("-")[0]
            if lang_code not in ("uz", "ru", "en"):
                lang_code = "uz"
            await user_api.create_user({
                "telegram_id": msg.from_user.id,
                "full_name": msg.from_user.full_name,
                "username": msg.from_user.username,
                "language": lang_code,
            })
            logger.info(f"[/start] new user created: {user_tag} lang={lang_code}")
        await state.delete()
        return await _render_profile(h, send=True)
    except Exception as e:
        logger.error(f"start_handler error: {e}")


# ── Profil ────────────────────────────────────────────────────────────────────

@cb("profile")
async def profile_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    return await _render_profile(h, send=False)


# ── Status: online ────────────────────────────────────────────────────────────

@cb("status_online")
async def status_online_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()
    logger.info(f"[status_online] user_id={call.from_user.id}")
    driver = await driver_api.get_driver_by_telegram_id(call.from_user.id)
    if not driver:
        logger.warning(f"[status_online] driver not found: user_id={call.from_user.id}")
        return await h.edit("not_driver", reply_markup=register_driver_inl(lang))
    await driver_api.update_driver_status(driver.id, "online")
    logger.info(f"[status_online] driver_id={driver.id} → online")
    await h.answer("status_changed_online")
    return await _render_profile(h, send=False)


# ── Status: offline ───────────────────────────────────────────────────────────

@cb("status_offline")
async def status_offline_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()
    logger.info(f"[status_offline] user_id={call.from_user.id}")
    driver = await driver_api.get_driver_by_telegram_id(call.from_user.id)
    if not driver:
        logger.warning(f"[status_offline] driver not found: user_id={call.from_user.id}")
        return await h.edit("not_driver", reply_markup=register_driver_inl(lang))

    if await order_api.has_active_orders(driver.id):
        logger.info(f"[status_offline] blocked — active orders exist: driver_id={driver.id}")
        return await h.answer("has_active_order", show_alert=True)

    await driver_api.update_driver_status(driver.id, "offline")
    logger.info(f"[status_offline] driver_id={driver.id} → offline")
    await h.answer("status_changed_offline")
    return await _render_profile(h, send=False)


# ── Yordam ────────────────────────────────────────────────────────────────────

@cb("help")
async def help_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()
    driver = await driver_api.get_driver_by_telegram_id(call.from_user.id)
    balance = f"{driver.amount:,}" if driver else "0"
    return await h.edit(
        "help_info",
        reply_markup=help_inl(lang),
        balance=balance,
    )


# ── Balans to'ldirish ─────────────────────────────────────────────────────────

@cb("top_up_balance")
async def top_up_balance_callback(call: types.CallbackQuery, state: StateContext, send=False):
    h = UltraHandler(call, state)
    lang = await h.lang()
    await h.set_state(BalanceState.upload)
    if send:
        await h.delete()
        return await h.send("top_up_request", reply_markup=choice_balance_inl(lang))
    return await h.edit("top_up_request", reply_markup=choice_balance_inl(lang))


# ── Buyurtmalarni qabul qilish ────────────────────────────────────────────────

@cb("accept_")
async def accept_order_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()
    _, order_type, order_id = call.data.split('_')
    logger.info(f"[accept_order] user_id={call.from_user.id} order_id={order_id} type={order_type}")
    try:
        order_info = OrderTypes.from_dict(await order_api.get_order(int(order_id)))
        text = _build_order_text(lang, order_info, order_info.creator.phone, is_travel=order_type == "travel")

        if order_info.status == "created" and order_info.driver_details is None:
            assigned = await order_api.add_new_driver(order_id, call.from_user.id)
            if assigned.get("status") == "assigned":
                logger.info(f"[accept_order] ASSIGNED order_id={order_id} → driver user_id={call.from_user.id}")
                loc = order_info.content_object.from_location.get("location", {})
                if loc.get("latitude") and loc.get("longitude"):
                    await h.location(loc["latitude"], loc["longitude"])
                return await h.edit(text, reply_markup=delete_inl(lang), translate=False)

        logger.info(f"[accept_order] order_id={order_id} already taken, status={order_info.status}")
        return await h.edit("order_taken_by_other", reply_markup=delete_inl(lang))
    except Exception as e:
        logger.error(f"accept_order_callback: order_id={order_id} user_id={call.from_user.id} error={e}")


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


# ── Navigatsiya ───────────────────────────────────────────────────────────────

@cb("back")
async def back_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    suffix = call.data.split('_')[-1]

    if suffix == "balance":
        await h.clear_state()
        return await help_callback(call, state)
    if suffix == "top":
        await h.clear_state()
        await h.set_state(stat=BalanceState.upload)
        return await top_up_balance_callback(call, state, send=True)

    # default: profil
    await h.clear_state()
    return await _render_profile(h, send=False)


@cb("cancel")
async def cancel_callback(call: types.CallbackQuery, state: StateContext):
    await UltraHandler(call, state).delete()


@cb("delete")
async def delete_callback(call: types.CallbackQuery, state: StateContext):
    await UltraHandler(call, state).delete()
