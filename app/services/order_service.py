from ..core.log import logger
from ..services.base import BaseService
from ..services.driver_service import driver_api


class OrderServiceAPI(BaseService):
    async def get_order(self, order_id):
        return await self._request('GET', f'/orders/{order_id}/driver/')

    async def update_status(self, order_id, status):
        return await self._request('PATCH', f'/orders/{order_id}/', json={'status': status})

    async def get_by_id(self, telegram_id):
        return await self._request('GET', f'/orders/user/{telegram_id}/')

    async def add_new_driver(self, order_id, telegram_id):
        try:
            driver = await driver_api.get_driver_by_telegram_id(telegram_id)
            return await self._request(
                'PATCH', f'/orders/{order_id}/',
                json={'driver': driver.id, 'status': 'assigned'},
            )
        except Exception as e:
            logger.error(f"add_new_driver(order={order_id}, tg={telegram_id}): {e}")

    async def get_active_orders(self, data):
        try:
            return await self._request('GET', '/orders/', params=data)
        except Exception as e:
            logger.error(f"get_active_orders: {e}")

    async def has_active_orders(self, driver_id: int) -> bool:
        try:
            for status in ("assigned", "arrived", "started"):
                result = await self._request('GET', '/orders/', params={
                    'driver': driver_id,
                    'status': status,
                })
                if result.get('count', 0) > 0:
                    return True
            return False
        except Exception as e:
            logger.error(f"has_active_orders({driver_id}): {e}")
            return False


order_api = OrderServiceAPI()
