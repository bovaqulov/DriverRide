from ..keyboards.base import kb
from ...core.config import settings


def main_menu_inl(lang, status="online"):
    keyword = kb(lang)

    keyword.data(status, status).row()
    keyword.data("settings", "settings")
    keyword.data("balance", "balance").row()
    keyword.data("help", "help")
    return keyword.inline()

def balance_inl(lang, balance=True):
    keyword = kb(lang)
    keyword.data("top_up_balance", "top_up_balance").row()
    if balance:
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

def settings_inl(lang):
    keyword = kb(lang)
    keyword.data("direction", "direction").row()
    keyword.data("phone_number", "phone_number").row()
    keyword.data("back", "back").row()
    return keyword.inline()

def confirm_order_inl(lang, order_id, travel=True):
    keyword = kb(lang)
    order_type = "travel" if travel else "delivery"
    keyword.data("accept_button", f"accept_{order_type}_{order_id}").row()
    return keyword.inline()

def chat_inl(lang, order_id):
    keyword = kb(lang)
    frontend_url = settings.FRONTEND_URL
    url = f"{frontend_url}/chat/{order_id}/"
    keyword.data("chat", "chat").row()
    keyword.data("arrived", f"arrived_{order_id}")
    return keyword.inline()


def back_inl(lang):
    keyword = kb(lang)
    keyword.data("back", "back").row()
    return keyword.inline()


def picked_up_inl(lang, order_id):
    keyword = kb(lang)
    keyword.data("picked_up", f"picked_{order_id}").row()
    return keyword.inline()


def finish_inl(lang, order_id):
    keyword = kb(lang)
    keyword.data("finish", f"finished_{order_id}").row()
    return keyword.inline()

def phone_number_rb(lang: str):
    keyboard = kb(lang)
    keyboard.contact("get_phone_number")
    return keyboard.reply()
