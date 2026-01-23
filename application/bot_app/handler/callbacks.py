import time
from datetime import timezone, timedelta, datetime

from telebot import types
from telebot.states.asyncio import StateContext

from ..handler.functions import main_menu
from ..handler.decorator import cb, UltraHandler, BalanceState
from ..keyboards.inline import balance_inl, choice_balance_inl, settings_inl, chat_inl, back_inl, picked_up_inl, \
    finish_inl, delete_inl
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
        order = await order_api.get_order(int(order_id))

        order_info = OrderTypes.from_dict(order)

        if order_type == "travel":
            text = _create_message_text(lang, order_info, use_phone=order_info.creator.phone)
        else:
            text = _create_text(lang, order_info, use_phone=order_info.creator.phone)

        if order_info.status == "created" and order_info.driver_details is None:

            assigned = await order_api.add_new_driver(order_id, call.from_user.id)
            if assigned.get("status") == "assigned":
                location = order_info.content_object.from_location.get("location")
                if location:
                    if location.get("latitude", None) and location.get("longitude", None):
                        await h.location(
                            location.get("latitude"),
                            location.get("longitude")
                        )
                return await h.edit(text, reply_markup=chat_inl(lang, order_id), translate=False)

        return await h.edit("order_taken_by_other", reply_markup=delete_inl(lang))
    except Exception as e:
        print(e)


def _create_message_text(lang, order: OrderTypes, use_phone) -> str:
    # Gender belgisi
    gender_icon = "👩" if order.content_object.has_woman else "👤"
    woman_note = t("woman_passenger_note", lang) if order.content_object.has_woman else ""

    # Price ni raqamga o'tkazish
    try:
        # Float ga o'tkazib, butun qismini olish
        price_num = float(order.content_object.price) * order.content_object.passenger
        formatted_price = f"{price_num:,.0f}"
    except (ValueError, TypeError):
        # Agar o'tkazish mummkin bo'lmasa, oddiy string qaytarish
        formatted_price = order.content_object.price * order.content_object.passenger

    print(order)

    return t("accepted_order_details", lang,
             travel_id=order.id,
             from_city=order.content_object.route.from_city.get("translate").get(lang),
             to_city=order.content_object.route.to_city.get("translate").get(lang),
             gender_icon=gender_icon,
             passenger=order.content_object.passenger,
             woman_note=woman_note,
             price=formatted_price,  # Endi formatlangan
             phone=use_phone,
             time=datetime.fromisoformat(order.content_object.start_time.replace('Z', '+00:00')).astimezone(timezone(timedelta(hours=5))).strftime("%d.%m.%Y, %H:%M"),
             comment=order.content_object.comment,
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
             from_city=order.content_object.route.from_city.get("translate").get(lang),
             to_city=order.content_object.route.to_city.get("translate").get(lang),
             price=formatted_price,
             phone=use_phone,
             comment=order.content_object.comment,
             time=datetime.fromisoformat(order.content_object.start_time.replace('Z', '+00:00')).astimezone(timezone(timedelta(hours=5))).strftime("%d.%m.%Y, %H:%M"),
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
    try:
        await driver_api.change_direction(driver_data.id, driver_data.route_id.route_id)
        await h.answer("change_direction")
        await main_menu(call, state)
    except Exception as e:
        print(e)


@cb("help")
async def help_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()
    return await h.edit(
        "contact_info",
        reply_markup=back_inl(lang)
    )


@cb("cancel")
async def cancel_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    await h.delete()


@cb("delete")
async def delete_callback(call: types.CallbackQuery, state: StateContext):
    h = UltraHandler(call, state)
    await h.delete()

# def create_active_order(orders, lang) -> str:
#     print(orders)
#     for order in orders.get("results", []):
#
#         order_price = t("order_price", lang, order_price=order.get("price", 0))
#         order_type = t("order_type", lang, order_type=order.get("order_type", ""))
#         if order.get("order_type", "") != "delivery":
#             order_passenger = t("order_passenger", lang, )
#
#     return ""
#
# @cb("active_orders")
# async def active_orders_callback(call: types.CallbackQuery, state: StateContext):
#     h = UltraHandler(call, state)
#     lang = await h.lang()
#     driver = await h.get_driver()
#     order_api = OrderServiceAPI()
#     orders = await order_api.get_active_orders(
#         {
#             "from_location": driver.from_location,
#             "to_location": driver.to_location,
#             "status": "created",
#             'travel_class': driver.car_class,
#         }
#     )
#
#     order_count = orders.get("count", 0)
#
#     if order_count == 0 or order_count < 0:
#         return await h.answer("no_active_orders")
#
#     text = create_active_order(orders, lang)
#
#     return await h.send(
#         text,
#         translate=True,
#
#     )
#
#
