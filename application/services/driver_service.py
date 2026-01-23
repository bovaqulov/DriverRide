from typing import Optional, Dict, Any
from ..core.log import logger
from ..services.base import BaseService
from ..services.types import DriverService, CarService, DriverTransactionService, convert_api_response_to_driver_service


class DriverServiceAPI(BaseService):
    """Driver API bilan ishlash uchun service klassi"""

    async def get_driver(self, driver_id: int) -> Optional[DriverService]:
        """Get driver by ID"""
        logger.info(f"Fetching driver by ID: {driver_id}")
        try:
            data = await self._request('GET', f'/drivers/{driver_id}/')

            if 'error' in data:
                logger.warning(f"API returned error for driver ID {driver_id}: {data['error']}")
                return None

            logger.debug(f"Successfully fetched driver ID {driver_id}")
            return self._dict_to_driver(data)
        except Exception as e:
            logger.error(f"Exception while fetching driver ID {driver_id}: {str(e)}")
            return None

    async def get_driver_by_telegram_id(self, telegram_id: int) -> Optional[DriverService]:
        """Get driver by telegram ID"""
        logger.info(f"Fetching driver by telegram_id: {telegram_id}")
        try:
            data = await self._request('GET', f'/drivers/by-telegram-id/{telegram_id}/')

            # Agar javob HTML (masalan, 500 xato) bo'lsa, 'error' kaliti bo'lmasa ham xato bo'lishi mumkin
            if isinstance(data, str) and data.strip().startswith('<!DOCTYPE'):
                logger.error(f"Unexpected HTML response for telegram_id {telegram_id}: {data[:200]}...")
                return None

            if 'error' in data or 'detail' in data and data.get('detail') == 'Not found.':
                logger.warning(f"Driver not found for telegram_id {telegram_id}: {data}")
                return None

            logger.debug(f"Successfully fetched driver with telegram_id {telegram_id}")
            return self._dict_to_driver(data)
        except Exception as e:
            logger.error(f"Exception while fetching driver by telegram_id {telegram_id}: {str(e)}")
            return None

    async def update_driver(self, driver_id: int, update_data: Dict[str, Any]) -> Optional[DriverService]:
        """Update driver"""
        logger.info(f"Updating driver ID {driver_id} with data: {update_data}")
        try:
            data = await self._request('PATCH', f'/drivers/{driver_id}/', json=update_data)

            if 'error' in data:
                logger.warning(f"Failed to update driver ID {driver_id}: {data['error']}")
                return None

            logger.info(f"Successfully updated driver ID {driver_id}")
            return self._dict_to_driver(data)
        except Exception as e:
            logger.error(f"Exception while updating driver ID {driver_id}: {str(e)}")
            return None

    async def list_drivers(self, filters: Optional[Dict[str, Any]] = None) -> dict:
        """Get drivers list with filters"""
        filter_str = str(filters) if filters else "no filters"
        logger.info(f"Fetching drivers list with {filter_str}")
        try:
            params = filters or {}
            data = await self._request('GET', '/drivers/', params=params)

            if 'error' in data:
                logger.warning(f"Failed to fetch drivers list: {data['error']}")
                return {}

            driver_count = len(data.get('results', data)) if isinstance(data, dict) and 'results' in data else len(data) if isinstance(data, list) else 0
            logger.debug(f"Successfully fetched drivers list (count: {driver_count})")
            return data
        except Exception as e:
            logger.error(f"Exception while fetching drivers list: {str(e)}")
            return {}

    async def change_direction(self, driver_id: int, route_id: str) -> None:
        """Change driver direction"""
        response = await self._request(
            'PATCH',
            f'/drivers/{driver_id}/update-route/',  # yoki /update-route/
            json={'route_id': route_id}
        )
        print(response)
    # Conversion methods
    def _dict_to_driver(self, data: Dict[str, Any]) -> DriverService:
        logger.debug("Converting API response to DriverService object")
        return convert_api_response_to_driver_service(data)


    async def add_driver_balance(self, driver_id: int, amount: float, reason: str = None) -> Optional[Dict[str, Any]]:
        """Haydovchining balansiga pul qo'shish"""
        logger.info(f"Adding balance to driver ID {driver_id}: amount={amount}, reason={reason}")

        try:
            # Transaction yaratish
            transaction_data = {
                'driver': driver_id,
                'amount': amount
            }

            # Transaction yaratish
            transaction_result = await self._request(
                'POST',
                '/transactions/',
                json=transaction_data
            )

            if 'error' in transaction_result:
                logger.warning(f"Failed to create transaction for driver {driver_id}: {transaction_result['error']}")
                return None

            # Haydovchining balansini yangilash
            update_result = await self._request(
                'PATCH',
                f'/drivers/{driver_id}/',
                json={'amount': amount}  # Bu amount ni qo'shib qo'yadi
            )

            if 'error' in update_result:
                logger.warning(f"Failed to update driver balance for ID {driver_id}: {update_result['error']}")
                return None

            logger.info(f"Successfully added {amount} to driver ID {driver_id}")

            return {
                'transaction': transaction_result,
                'driver': update_result,
                'amount_added': amount
            }

        except Exception as e:
            logger.error(f"Exception while adding balance to driver {driver_id}: {str(e)}")
            return None

    async def add_balance_by_telegram_id(self, telegram_id: int, amount: float, reason: str = None) -> Optional[
        Dict[str, Any]]:
        """Telegram ID bo'yicha haydovchining balansiga pul qo'shish"""
        logger.info(f"Adding balance to driver by telegram_id {telegram_id}: amount={amount}")

        try:
            # Haydovchini telegram_id orqali topish
            driver = await self.get_driver_by_telegram_id(telegram_id)
            if not driver:
                logger.warning(f"Driver not found with telegram_id {telegram_id}")
                return None

            # Balans qo'shish
            return await self.add_driver_balance(driver.id, driver.amount + amount, reason)

        except Exception as e:
            logger.error(f"Exception while adding balance to driver by telegram_id {telegram_id}: {str(e)}")
            return None