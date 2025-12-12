from application.services.base import BaseService
from application.services.driver_service import DriverServiceAPI


class OrderServiceAPI(BaseService):
    async def get(self, order_id):
        return await self._request(
            "GET",
            f"/orders/{order_id}",
        )

    async def update_status(self, order_id, status):
        return await self._request(
            "PATCH",
            f"/orders/{order_id}/",
            json={'status': status},
        )
    async def get_by_id(self, telegram_id):
        return await self._request(
            "GET",
            f"/orders/user/{telegram_id}/",
        )

    async def add_new_driver(self, order_id, telegram_id):
        try:
            driver = await DriverServiceAPI().get_driver_by_telegram_id(telegram_id)
            print(driver)
            return await self._request(
                "PATCH",
                f"/orders/{order_id}/",
                json={'driver': driver.id, "status": "assigned"},
            )
        except Exception as e:
            print("Misatke is me: ", e)

    async def get_active_orders(self, data):
        try:
            return await self._request(
                "GET",
                "/orders",
                data=data,
            )
        except Exception as e:
            print("Misatke is me: ", e)