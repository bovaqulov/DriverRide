import json
import asyncio
from typing import List
from dataclasses import dataclass

from .api_types import OrderTypes, OrderStatus
from ..bot_app.keyboards.inline import confirm_order_inl, finish_inl
from ..core.i18n import t
from ..core.bot import bot
from ..services import TelegramUser
from ..services.driver_service import DriverServiceAPI


@dataclass
class MessageTask:
    """Message jo'natish vazifasi"""
    telegram_id: int
    text: str
    reply_markup: dict
    retry_count: int = 0


class MessageQueue:
    """Message queue manager"""

    def __init__(self, max_workers: int = 5, batch_size: int = 10):
        self.queue = asyncio.Queue()
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.is_running = False
        self.workers = []

    async def start(self):
        """Queue ishga tushirish"""
        if not self.is_running:
            self.is_running = True
            # Bir nechta workerlar yaratish
            for i in range(self.max_workers):
                worker = asyncio.create_task(self._worker(f"worker-{i}"))
                self.workers.append(worker)
            print(f"MessageQueue started with {self.max_workers} workers")

    async def stop(self):
        """Queue to'xtatish"""
        self.is_running = False
        # Wait for all workers to complete
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

    async def add_message(self, message_task: MessageTask):
        """Queuega message qo'shish"""
        await self.queue.put(message_task)

    async def _worker(self, name: str):
        """Worker function"""
        while self.is_running:
            try:
                # Batch olish
                batch = []
                for _ in range(self.batch_size):
                    try:
                        # Timeout bilan olish
                        task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                        batch.append(task)
                    except asyncio.TimeoutError:
                        break

                if batch:
                    # Batch message jo'natish
                    await self._process_batch(batch)

                    # Tasklarni queue dan chiqarish
                    for task in batch:
                        self.queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {name} error: {e}")
                await asyncio.sleep(1)

    async def _process_batch(self, batch: List[MessageTask]):
        """Batch message jo'natish"""
        tasks = []
        for message_task in batch:
            task = self._send_single_message(
                message_task.telegram_id,
                message_task.text,
                message_task.reply_markup,
                message_task.retry_count
            )
            tasks.append(task)

        # Barcha message lar parallel jo'natiladi
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Xatolarni qayta ishlash
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                message_task = batch[i]
                if message_task.retry_count < 3:
                    message_task.retry_count += 1
                    await self.add_message(message_task)
                    print(f"Retrying message to {message_task.telegram_id}, attempt {message_task.retry_count}")
                else:
                    print(f"Failed to send message to {message_task.telegram_id} after 3 attempts")

    async def _send_single_message(self, telegram_id: int, text: str, reply_markup: dict, retry_count: int):
        """Bitta message jo'natish"""
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=text,
                reply_markup=reply_markup
            )
            print(f"Message sent to {telegram_id}")
            return True
        except Exception as e:
            print(f"Error sending to {telegram_id}: {e}")
            return e


class OrderResponse:
    def __init__(self, request):
        self.driver_api = DriverServiceAPI()
        self.request = request
        self.message_queue = MessageQueue(max_workers=3, batch_size=5)
        self._queue_started = False

    async def _ensure_queue_started(self):
        """Queue ishlashini ta'minlash"""
        if not self._queue_started:
            await self.message_queue.start()
            self._queue_started = True

    async def _order(self) -> OrderTypes:
        """Buyurtma ma'lumotlarini olish"""
        try:
            response = await self.request.body()
            result = response.decode("utf-8")
            data = json.loads(result)
            print(f"Order data received: {data}")
            return OrderTypes.from_dict(data)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return
        except Exception as e:
            print(f"Error parsing order: {e}")
            return

    async def control(self):
        """Asosiy control funksiyasi"""
        try:
            order: OrderTypes = await self._order()
            if order.status == OrderStatus.CREATED.value:
                # Queue ishlashini ta'minlash
                await self._ensure_queue_started()

                # Driverlarni topish
                drivers = await self._find_matching_drivers(order)
                print(f"Found {len(drivers)} drivers for order {order.id}")

                # Message larni queue ga qo'shish
                for driver in drivers:
                    await self._passenger_create(driver, order)

            if order.status == OrderStatus.STARTED.value:
                await self._ensure_queue_started()
                lang = await TelegramUser().get_lang(order.driver_details.telegram_id)
                return await bot.send_message(
                    order.driver_details.telegram_id,
                    t("safe_trip", lang),
                    reply_markup=finish_inl(lang, order.id)
                )



        except Exception as e:
            print(f"Error in OrderResponse.control: {e}")

    def _create_travel_message(self, order, lang):
        gender_icon = "👩" if order.content_object.has_woman else "👤"
        woman_note = t("woman_passenger_note", lang) if order.content_object.has_woman else ""

        text = t("new_trip_request", lang,
                 travel_id=order.id,
                 from_city=order.from_city.title(),
                 to_city=order.to_city.title(),
                 gender_icon=gender_icon,
                 passenger=order.content_object.passenger,
                 woman_note=woman_note,
                 price=order.content_object.price)
        return text

    def _create_delivery_message(self, order, lang):
        text = t("new_delivery_request", lang,
                 travel_id=order.id,
                 from_city=order.from_city.title(),
                 to_city=order.to_city.title(),
                 price=order.content_object.price)

        return text

    async def _passenger_create(self, driver: dict, order: OrderTypes):
        """Message tayyorlash va queue ga qo'shish"""
        try:
            driver_info = driver.get("driver_info", {})
            telegram_id = driver_info.get("telegram_id")

            if not telegram_id:
                print("Driver has no telegram_id")
                return

            lang = driver_info.get("language", "uz")

            # Text tayyorlash
            if order.content_type_name == "passengerpost":
                text = self._create_delivery_message(order, lang)
                reply_markup = confirm_order_inl(lang, order.id, travel=False)
            else:
                text = self._create_travel_message(order, lang)
                reply_markup = confirm_order_inl(lang, order.id)


            # Queue ga qo'shish
            message_task = MessageTask(
                telegram_id=telegram_id,
                text=text,
                reply_markup=reply_markup
            )

            await self.message_queue.add_message(message_task)
            print(f"Message queued for driver {telegram_id}")

        except Exception as e:
            print(f"Error preparing message for driver: {e}")

    async def _find_matching_drivers(self, order: OrderTypes) -> List[dict]:
        """Mos keladigan haydovchilarni topish"""
        params = {
            "from_location": order.from_city,
            "to_location": order.to_city,
            "status": "online",
            "min_amount": int(int(order.content_object.price) * 0.05),
            "ordering": "-amount",
            "exclude_busy": "true",
        }

        CAR_CLASS_MAP = {
            "economy": ["economy"],
            "standard": ["standard", "comfort"],
            "comfort": ["comfort"],
        }

        travel_class = order.content_object.travel_class

        if travel_class and travel_class.lower() != "all":
            params["car_class"] = CAR_CLASS_MAP.get(travel_class.lower())

        try:
            response = await self.driver_api.list_drivers(params)
            return response.get("results", {})
        except Exception as e:
            print(f"Error finding drivers: {e}")
            return []

    async def cleanup(self):
        """Tozalash ishlari"""
        if self._queue_started:
            await self.message_queue.stop()
            self._queue_started = False