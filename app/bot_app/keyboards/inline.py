from ..keyboards.base import kb
from ...core.config import settings


def profile_inl(lang, status="offline"):
    keyword = kb(lang)
    keyword.web_app("web_panel", settings.FRONTEND_URL).row()
    if status == "offline":
        keyword.data("go_online", "status_online").row()
    elif status == "online":
        keyword.data("go_offline", "status_offline").row()
    # on_the_way: tizim o'rnatadi, haydovchi o'zgartira olmaydi
    keyword.data("help", "help").row()
    return keyword.inline()


def help_inl(lang):
    keyword = kb(lang)
    keyword.data("top_up_balance", "top_up_balance").row()
    keyword.data("back", "back").row()
    return keyword.inline()


def register_driver_inl(lang):
    keyword = kb(lang)
    keyword.url("register", "https://t.me/gozdekyurbot").row()
    return keyword.inline()


def choice_balance_inl(lang):
    keyword = kb(lang)
    keyword.data("70,000", "sum_70")
    keyword.data("140,000", "sum_140").row()
    keyword.data("210,000", "sum_210")
    keyword.data("280,000", "sum_280").row()
    keyword.data("back", "back_balance")
    return keyword.inline()


def payment_inl(lang):
    keyword = kb(lang)
    keyword.pay("pay").row()
    keyword.data("back", "back_top").row()
    return keyword.inline()


def confirm_order_inl(lang, order_id, travel=True):
    keyword = kb(lang)
    order_type = "travel" if travel else "delivery"
    keyword.data("accept_button", f"accept_{order_type}_{order_id}")
    keyword.data("cancel", "cancel")
    return keyword.inline()


def back_inl(lang):
    keyword = kb(lang)
    keyword.data("back", "back").row()
    return keyword.inline()


def delete_inl(lang):
    keyword = kb(lang)
    keyword.data("delete_message", "delete").row()
    return keyword.inline()
