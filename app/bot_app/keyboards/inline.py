from ..keyboards.base import kb


def main_menu_inl(lang, status="online"):
    keyword = kb(lang)
    keyword.data("balance", "balance").row()
    keyword.data("help", "help").row()
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
