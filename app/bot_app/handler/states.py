from telebot.states.asyncio import StateContext
from telebot.types import CallbackQuery

from ..handler import UltraHandler
from ..handler.decorator import state, BalanceState
from ..keyboards.inline import choice_balance_inl, payment_inl


@state(state=BalanceState.upload)
async def balance_state_upload(call, state: StateContext):
    h = UltraHandler(call, state)
    lang = await h.lang()

    if isinstance(call, CallbackQuery):
        await h.delete()
        amount = int(f"{call.data.split('_')[-1]}000")
    else:
        await h.delete(count=2)
        if not call.text.isdigit():
            return await h.send(
                "errors.only_numbers",
                reply_markup=choice_balance_inl(lang)
            )
        else:
            amount = int(call.text)
            if 0 < amount <= 25000:
                return await h.send(
                    "min_payment",
                    reply_markup=choice_balance_inl(lang)
                )

    return await h.invoice(
        "top_up_title",
        "balance_notice",
        prices=amount * 100,
        payload = f"driver:{call.from_user.id}:amount:{amount}",
        reply_markup=payment_inl(lang)
    )
