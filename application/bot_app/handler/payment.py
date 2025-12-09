from application.bot_app.handler import UltraHandler
from application.bot_app.keyboards.inline import back_inl
from application.core import bot, t, logger
from application.services.driver_service import DriverServiceAPI


@bot.shipping_query_handler(func=lambda query: True)
async def shipping(shipping_query):
    print(shipping_query)
    await bot.answer_shipping_query(shipping_query.id, ok=True,
                              error_message='Oh, seems like our Dog couriers are having a lunch right now. Try again later!')


@bot.pre_checkout_query_handler(func=lambda query: True)
async def checkout(pre_checkout_query):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
                                                " try to pay again in a few minutes, we need a small rest.")


@bot.message_handler(content_types=['successful_payment'])
async def got_payment(message):
    h = UltraHandler(message)
    lang = await h.lang()

    try:
        # Payment ma'lumotlarini olish
        payment_info = message.successful_payment

        # Invoice payload ni pars qilish
        # Masalan: invoice_payload="driver_123" formatida bo'lishi mumkin
        invoice_payload = payment_info.invoice_payload

        # Qaysi haydovchiga pul qo'shilishini aniqlash
        # Misol uchun: payload="driver:123:amount:50000"
        if "driver:" in invoice_payload:
            parts = invoice_payload.split(":")
            if len(parts) >= 2:
                driver_telegram_id = int(parts[1])
                amount = float(payment_info.total_amount) / 100 # Telegram amount ni minor unitlarda yuboradi

                # DriverServiceAPI orqali balans qo'shish
                driver_service = DriverServiceAPI()

                result = await driver_service.add_balance_by_telegram_id(
                    telegram_id=driver_telegram_id,
                    amount=amount,
                    reason=f"Telegram payment: {payment_info.telegram_payment_charge_id}"
                )

                if result:
                    # Muvaffaqiyatli xabar
                    await bot.send_message(
                        message.from_user.id,
                        text=t("payment_success_with_balance", lang=lang).format(
                            amount=amount,
                            new_balance=result['driver'].get('amount', 0)
                        ),
                        reply_markup=back_inl(lang)
                    )

                    # Haydovchiga ham xabar yuborish
                    try:
                        await bot.send_message(
                            driver_telegram_id,
                            text=t("driver_balance_added", lang=lang).format(
                                amount=amount,
                                total_balance=result['driver'].get('amount', 0),
                                payment_id=payment_info.telegram_payment_charge_id
                            )
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify driver: {str(e)}")
                else:
                    # Balans qo'shishda xatolik
                    await bot.send_message(
                        message.from_user.id,
                        text=t("payment_success_but_balance_error", lang=lang),
                        reply_markup=back_inl(lang)
                    )
            else:
                # Invalid payload
                await bot.send_message(
                    message.from_user.id,
                    text=t("payment_success_invalid_payload", lang=lang),
                    reply_markup=back_inl(lang)
                )
        else:
            # Oddiy payment
            await bot.send_message(
                message.from_user.id,
                text=t("payment_success", lang=lang),
                reply_markup=back_inl(lang)
            )

    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        await bot.send_message(
            message.from_user.id,
            text=t("payment_error", lang=lang),
            reply_markup=back_inl(lang)
        )