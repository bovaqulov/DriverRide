import time
from dataclasses import asdict

from telebot import types
from telebot.states.asyncio import StateContext

from ..handler.functions import main_menu
from ..handler.decorator import cb, UltraHandler, BalanceState
from ..keyboards.inline import balance_inl, choice_balance_inl, settings_inl, chat_inl, back_inl, picked_up_inl, \
    finish_inl
from ...api.api_types import OrderTypes

from ...core.i18n import t
from ...services.city_service import CityServiceAPI
from ...services.driver_service import DriverServiceAPI
from ...services.order_service import OrderServiceAPI
from ...services.types import DriverService


@cb("offline")
async def offline_callback(
        call: types.CallbackQuery, state: StateContext
):
    return await main_menu(call, state, status="online")


@cb("online")
async def online_callback(
        call: types.CallbackQuery, state: StateContext
):

    return await main_menu(call, state, status="offline")


@cb("balance")
async def balance_callback(
        call: types.CallbackQuery, state: StateContext
):
    h = UltraHandler(call, state)
    lang = await h.lang()

    balance: DriverService = await DriverServiceAPI().get_driver_by_telegram_id(call.message.chat.id)

    return await h.edit(
        "account_balance_info",
        reply_markup=balance_inl(lang),
        balance=f"{balance.amount:,}",
    )


@cb("back")
async def back_callback(
        call: types.CallbackQuery, state: StateContext
):
    h = UltraHandler(call, state)
    page: list = call.data.split('_')

    if 1 == len(page):
        return await main_menu(call, state)
    elif "balance" == page[-1]:
        await h.clear_state()
        return await balance_callback(call, state)
    elif "top" == page[-1]:
        await h.clear_state()
        await h.set_state(stat=BalanceState.upload)
        await top_up_balance_callback(call, state, send=True)


@cb("top_up_balance")
async def top_up_balance_callback(
        call: types.CallbackQuery, state: StateContext, send=False
):
    h = UltraHandler(call, state)
    lang = await h.lang()
    await h.set_state(BalanceState.upload)

    if send:
        await h.delete()
        func = h.send
    else:
        func = h.edit

    return await func(
        "top_up_request",
        reply_markup=choice_balance_inl(lang)
    )


@cb("settings")
async def settings_callback(
        call: types.CallbackQuery, state: StateContext
):
    h = UltraHandler(call, state)
    lang = await h.lang()
    return await h.edit(
        "settings",
        reply_markup=settings_inl(lang)
    )


@cb("accept_")
async def accept_order_callback(
        call: types.CallbackQuery, state: StateContext
):
    h = UltraHandler(call, state)
    lang = await h.lang()

    data, order_type, order_id = call.data.split('_')
    try:
        order_api = OrderServiceAPI()
        order = await order_api.get(int(order_id))
        order_info = OrderTypes.from_dict(order)

        if order_type == "travel":
            text = _create_message_text(lang, order_info, use_phone=order_info.creator.phone)
        else:
            text = _create_text(lang, order_info, use_phone=order_info.creator.phone)

        if order_info.status == "created" and order_info.driver is None:

            assigned = await order_api.add_new_driver(order_id, call.from_user.id)

            if assigned.get("status") == "assigned":
                if location := order_info.content_object.from_location.get("location", None):


                    await h.location(
                        location.get("latitude"),
                        location.get("longitude")
                    )
                return await h.edit(text, reply_markup=chat_inl(lang, order_id))

        return await h.edit("order_taken_by_other", reply_markup=back_inl(lang))
    except Exception as e:
        print(e)


def _create_message_text(lang, order: OrderTypes, use_phone) -> str:
    # Gender belgisi
    gender_icon = "👩" if order.content_object.has_woman else "👤"
    woman_note = t("woman_passenger_note", lang) if order.content_object.has_woman else ""

    # Price ni raqamga o'tkazish
    try:
        # Float ga o'tkazib, butun qismini olish
        price_num = float(order.content_object.price)
        formatted_price = f"{price_num:,.0f}"
    except (ValueError, TypeError):
        # Agar o'tkazish mummkin bo'lmasa, oddiy string qaytarish
        formatted_price = order.content_object.price

    return t("accepted_order_details", lang,
             travel_id=order.id,
             from_city=order.from_city.title(),
             to_city=order.to_city.title(),
             gender_icon=gender_icon,
             passenger=order.content_object.passenger,
             woman_note=woman_note,
             travel_class=order.content_object.travel_class.title(),
             price=formatted_price,  # Endi formatlangan
             phone=use_phone,
             time=time.strftime('%H:%M')
             )

def _create_text(lang, order: OrderTypes, use_phone) -> str:
    try:
        # Float ga o'tkazib, butun qismini olish
        price_num = float(order.content_object.price)
        formatted_price = f"{price_num:,.0f}"
    except (ValueError, TypeError):
        # Agar o'tkazish mummkin bo'lmasa, oddiy string qaytarish
        formatted_price = order.content_object.price

    return t("accepted_order", lang,
             travel_id=order.id,
             from_city=order.from_city.title(),
             to_city=order.to_city.title(),
             price=formatted_price,
             phone=use_phone,
             time=time.strftime('%H:%M')
             )


@cb("chat")
async def chat_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()
    return await h.send("chat_deployment")


@cb("arrived_")
async def arrived_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()
    data, order_id = call.data.split('_')
    order_api = OrderServiceAPI()
    await order_api.update_status(int(order_id), "arrived")
    return await h.send(
        "send_arrived_info",
        reply_markup=picked_up_inl(lang, order_id)
    )

@cb("picked")
async def picked_up_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)

    lang = await h.lang()

    data, order_id = call.data.split('_')

    order_api = OrderServiceAPI()
    await order_api.update_status(int(order_id), "started")

    return await h.edit(
        "safe_trip",
        reply_markup=finish_inl(lang, order_id)
    )


@cb("finished")
async def finish_callback(call: types.CallbackQuery, state: StateContext):

    h = UltraHandler(call, state)
    data, order_id = call.data.split('_')
    order_api = OrderServiceAPI()
    await order_api.update_status(int(order_id), "ended")

    return await h.edit(
        "great"
    )

@cb("direction")
async def direction_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    driver_api = DriverServiceAPI()
    driver_data = await driver_api.get_driver_by_telegram_id(call.from_user.id)
    print(driver_data)
    try:
        city_api = CityServiceAPI()
        from_location_id = await city_api.get_id_city_title(driver_data.from_location)
        to_location_id = await city_api.get_id_city_title(driver_data.to_location)

        await driver_api.update_driver(driver_data.id, {
            "from_location": to_location_id,
            "to_location": from_location_id,
        })
        await h.answer("change_direction")
        await main_menu(call, state)
    except Exception as e:
        print(e)


