from typing import Any

from ..core.log import logger
from ..services.base import BaseService
from ..services.types import DriverService


class DriverServiceAPI(BaseService):
    async def get_driver(self, driver_id: int) -> DriverService | None:
        try:
            data = await self._request('GET', f'/drivers/{driver_id}/')
            return None if 'error' in data else DriverService.model_validate(data)
        except Exception as e:
            logger.error(f"get_driver({driver_id}): {e}")
            return None

    async def get_driver_by_telegram_id(self, telegram_id: int) -> DriverService | None:
        try:
            data = await self._request('GET', f'/drivers/by-telegram-id/{telegram_id}/')
            if 'error' in data or data.get('detail') in ('Not found', 'Not found.'):
                return None
            return DriverService.model_validate(data)
        except Exception as e:
            logger.error(f"get_driver_by_telegram_id({telegram_id}): {e}")
            return None

    async def update_driver(self, driver_id: int, update_data: dict[str, Any]) -> DriverService | None:
        try:
            data = await self._request('PATCH', f'/drivers/{driver_id}/', json=update_data)
            return None if 'error' in data else DriverService.model_validate(data)
        except Exception as e:
            logger.error(f"update_driver({driver_id}): {e}")
            return None

    async def list_drivers(self, filters: dict[str, Any] | None = None) -> dict:
        try:
            return await self._request('GET', '/drivers/', params=filters or {})
        except Exception as e:
            logger.error(f"list_drivers: {e}")
            return {}

    async def update_driver_status(self, driver_id: int, status: str) -> DriverService | None:
        try:
            data = await self._request('PATCH', f'/drivers/{driver_id}/update_status/', json={'status': status})
            return None if 'error' in data else DriverService.model_validate(data)
        except Exception as e:
            logger.error(f"update_driver_status({driver_id}, {status}): {e}")
            return None

    async def change_direction(self, driver_id: int, route_id: str) -> None:
        await self._request(
            'PATCH', f'/drivers/{driver_id}/update-route/', json={'route_id': route_id}
        )

    async def add_driver_balance(self, driver_id: int, amount: float, reason: str | None = None) -> dict | None:
        # WARNING: two separate API calls — not atomic. If the PATCH succeeds but the POST
        # already completed, a retry will create a duplicate transaction. The backend should
        # expose a single atomic endpoint (e.g. POST /drivers/{id}/add-balance/) to fix this.
        try:
            tx = await self._request('POST', '/transactions/', json={'driver': driver_id, 'amount': amount})
            if 'error' in tx:
                return None
            update = await self._request('PATCH', f'/drivers/{driver_id}/', json={'amount': amount})
            if 'error' in update:
                return None
            return {'transaction': tx, 'driver': update, 'amount_added': amount}
        except Exception as e:
            logger.error(f"add_driver_balance({driver_id}): {e}")
            return None

    async def add_balance_by_telegram_id(self, telegram_id: int, amount: float, reason: str | None = None) -> dict | None:
        try:
            driver = await self.get_driver_by_telegram_id(telegram_id)
            if not driver:
                return None
            return await self.add_driver_balance(driver.id, driver.amount + amount, reason)
        except Exception as e:
            logger.error(f"add_balance_by_telegram_id({telegram_id}): {e}")
            return None


driver_api = DriverServiceAPI()
