import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List
from dataclasses import dataclass

from .api_types import OrderTypes, OrderStatus, PassengerTypes
from ..bot_app.keyboards.inline import confirm_order_inl
from ..core.i18n import t
from ..core.bot import bot
from ..core.log import logger
from ..services import TelegramUserServiceAPI
from ..services.driver_service import DriverServiceAPI


@dataclass
class MessageTask:
    telegram_id: int
    text: str
    reply_markup: dict
    retry_count: int = 0


class MessageQueue:
    """Message queue manager — modul darajasida yagona instance."""

    def __init__(self, max_workers: int = 5, batch_size: int = 10):
        self.queue = asyncio.Queue()
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.is_running = False
        self.workers: List[asyncio.Task] = []

    async def start(self):
        if not self.is_running:
            self.is_running = True
            for i in range(self.max_workers):
                worker = asyncio.create_task(self._worker(f"worker-{i}"))
                self.workers.append(worker)
            logger.info(f"MessageQueue started with {self.max_workers} workers")

    async def stop(self):
        self.is_running = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

    async def add_message(self, message_task: MessageTask):
        await self.queue.put(message_task)

    async def _worker(self, name: str):
        while self.is_running:
            try:
                batch = []
                for _ in range(self.batch_size):
                    try:
                        task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                        batch.append(task)
                    except asyncio.TimeoutError:
                        break

                if batch:
                    await self._process_batch(batch)
                    for _ in batch:
                        self.queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {name} error: {e}")
                await asyncio.sleep(1)

    async def _process_batch(self, batch: List[MessageTask]):
        tasks = [
            self._send_single_message(t.telegram_id, t.text, t.reply_markup, t.retry_count)
            for t in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                msg = batch[i]
                if msg.retry_count < 3:
                    msg.retry_count += 1
                    await self.add_message(msg)
                    logger.warning(f"Retry {msg.retry_count}/3 for telegram_id={msg.telegram_id}")
                else:
                    logger.error(f"Failed after 3 attempts: telegram_id={msg.telegram_id}")

    async def _send_single_message(self, telegram_id: int, text: str, reply_markup, retry_count: int):
        try:
            await bot.send_message(chat_id=telegram_id, text=text, reply_markup=reply_markup)
            return True
        except Exception as e:
            logger.error(f"Send error telegram_id={telegram_id}: {e}")
            return e


# ── Modul darajasida yagona MessageQueue ────────────────────────────────────
_message_queue = MessageQueue(max_workers=3, batch_size=5)


async def start_message_queue():
    """App startup da bir marta chaqiriladi."""
    await _message_queue.start()


async def stop_message_queue():
    """App shutdown da bir marta chaqiriladi."""
    await _message_queue.stop()


class OrderResponse:
    def __init__(self, request):
        self.driver_api = DriverServiceAPI()
        self.request = request

    async def _order(self) -> OrderTypes:
        try:
            response = await self.request.body()
            data = json.loads(response.decode("utf-8"))
            order = OrderTypes.from_dict(data)
            logger.info(f"Order received: id={getattr(order, 'id', '?')} status={getattr(order, 'status', '?')}")
            return order
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing order: {e}")
            raise

    async def control(self):
        try:
            order: OrderTypes = await self._order()
            if order.status == OrderStatus.CREATED.value:
                drivers = await self._find_matching_drivers(order)
                logger.info(f"Found {len(drivers)} drivers for order {order.id}")
                for driver in drivers:
                    await self._passenger_create(driver, order)
        except Exception as e:
            logger.error(f"OrderResponse.control error: {e}")

    def _create_travel_message(self, order: OrderTypes, lang: str) -> str:
        try:
            gender_icon = "👩" if order.content_object.has_woman else "👤"
            woman_note = t("woman_passenger_note", lang) if order.content_object.has_woman else ""
            price = int(order.content_object.price) * int(order.content_object.passenger)
            return t("new_trip_request", lang,
                     order_id=order.id,
                     from_city=order.content_object.route.from_city.get("translate", {}).get(lang, ""),
                     to_city=order.content_object.route.to_city.get("translate", {}).get(lang, ""),
                     gender_icon=gender_icon,
                     cashback=order.content_object.cashback,
                     total_price=price - int(order.content_object.cashback),
                     passenger=order.content_object.passenger,
                     woman_note=woman_note,
                     comment=order.content_object.comment,
                     start_time=datetime.fromisoformat(
                         order.content_object.start_time.replace('Z', '+00:00')
                     ).astimezone(timezone(timedelta(hours=5))).strftime("%d.%m.%Y, %H:%M"),
                     price=price)
        except Exception as e:
            logger.error(f"_create_travel_message error: {e}")
            return ""

    def _create_delivery_message(self, order: OrderTypes, lang: str) -> str:
        try:
            return t("new_delivery_request", lang,
                     order_id=order.id,
                     cashback=order.content_object.cashback,
                     total_price=int(order.content_object.price) - int(order.content_object.cashback),
                     from_city=order.content_object.route.from_city.get("translate", {}).get(lang, ""),
                     to_city=order.content_object.route.to_city.get("translate", {}).get(lang, ""),
                     comment=order.content_object.comment,
                     start_time=datetime.fromisoformat(
                         order.content_object.start_time.replace('Z', '+00:00')
                     ).astimezone(timezone(timedelta(hours=5))).strftime("%d.%m.%Y, %H:%M"),
                     price=order.content_object.price)
        except Exception as e:
            logger.error(f"_create_delivery_message error: {e}")
            return ""

    async def _passenger_create(self, driver: dict, order: OrderTypes):
        try:
            driver_info = driver.get("driver_info", {})
            telegram_id = driver_info.get("telegram_id")
            if not telegram_id:
                logger.warning("Driver has no telegram_id, skipping")
                return

            lang = driver_info.get("language", "uz")

            if order.order_type == "travel":
                text = self._create_travel_message(order, lang)
                reply_markup = confirm_order_inl(lang, order.id)
            else:
                text = self._create_delivery_message(order, lang)
                reply_markup = confirm_order_inl(lang, order.id, travel=False)

            if not text:
                logger.error(f"Empty message text for driver {telegram_id}, skipping")
                return

            await _message_queue.add_message(MessageTask(
                telegram_id=telegram_id,
                text=text,
                reply_markup=reply_markup,
            ))
            logger.info(f"Message queued for driver {telegram_id}")

        except Exception as e:
            logger.error(f"_passenger_create error: {e}")

    async def _find_matching_drivers(self, order: OrderTypes) -> List[dict]:
        try:
            params = {
                "route_id": order.content_object.route.route_id,
                "status": "online",
                "min_amount": int((int(order.content_object.price) * int(order.content_object.passenger)) * 0.05),
                "ordering": "-amount",
                "exclude_busy": "true",
            }
            if order.content_object.tariff_id != 4:
                params["tariff_id"] = order.content_object.tariff_id

            response = await self.driver_api.list_drivers(params)
            return response.get("results", [])
        except Exception as e:
            logger.error(f"_find_matching_drivers error: {e}")
            return []
