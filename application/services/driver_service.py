from typing import Optional, Dict, Any, List
from dataclasses import asdict

from ..core.config import settings
from ..core.log import logger
from ..services.base import BaseService
from ..services.types import DriverService, CarService, DriverTransactionService


class DriverServiceAPI(BaseService):
    """Driver API bilan ishlash uchun service klassi"""

    async def get_driver(self, driver_id: int) -> Optional[DriverService]:
        """Get driver by ID"""
        try:
            data = await self._request('GET', f'/drivers/{driver_id}/')

            if 'error' in data:
                logger.warning(f"Error getting driver {driver_id}: {data['error']}")
                return None

            return self._dict_to_driver(data)
        except Exception as e:
            logger.error(f"Error getting driver {driver_id}: {str(e)}")
            return None

    async def get_driver_by_telegram_id(self, telegram_id: int) -> Optional[DriverService]:
        """Get driver by telegram ID"""
        try:
            data = await self._request('GET', '/drivers/by_telegram_id/', params={'telegram_id': telegram_id})

            if 'error' in data:
                logger.warning(f"Error getting driver by telegram_id {telegram_id}: {data['error']}")
                return None

            return self._dict_to_driver(data)
        except Exception as e:
            logger.error(f"Error getting driver by telegram_id {telegram_id}: {str(e)}")
            return None

    async def create_driver(self, driver_data: Dict[str, Any]) -> Optional[DriverService]:
        """Create new driver"""
        try:
            data = await self._request('POST', '/drivers/', json=driver_data)

            if 'error' in data:
                logger.warning(f"Error creating driver: {data['error']}")
                return None

            return self._dict_to_driver(data)
        except Exception as e:
            logger.error(f"Error creating driver: {str(e)}")
            return None

    async def update_driver(self, driver_id: int, update_data: Dict[str, Any]) -> Optional[DriverService]:
        """Update driver"""
        try:
            data = await self._request('PATCH', f'/drivers/{driver_id}/', json=update_data)

            if 'error' in data:
                logger.warning(f"Error updating driver {driver_id}: {data['error']}")
                return None

            return self._dict_to_driver(data)
        except Exception as e:
            logger.error(f"Error updating driver {driver_id}: {str(e)}")
            return None

    async def delete_driver(self, driver_id: int) -> bool:
        """Delete driver"""
        try:
            await self._request('DELETE', f'/drivers/{driver_id}/')
            return True
        except Exception as e:
            logger.error(f"Error deleting driver {driver_id}: {str(e)}")
            return False

    async def update_driver_status(self, driver_id: int, status: str) -> Optional[DriverService]:
        """Update driver status"""
        try:
            data = await self._request('PATCH', f'/drivers/{driver_id}/update_status/', json={'status': status})

            if 'error' in data:
                logger.warning(f"Error updating driver status {driver_id}: {data['error']}")
                return None

            return self._dict_to_driver(data)
        except Exception as e:
            logger.error(f"Error updating driver status {driver_id}: {str(e)}")
            return None

    async def get_driver_cars(self, driver_id: int) -> List[CarService]:
        """Get driver's cars"""
        try:
            data = await self._request('GET', f'/drivers/{driver_id}/cars/')

            if 'error' in data:
                logger.warning(f"Error getting driver cars {driver_id}: {data['error']}")
                return []

            return [self._dict_to_car(car_data) for car_data in data]
        except Exception as e:
            logger.error(f"Error getting driver cars {driver_id}: {str(e)}")
            return []

    async def search_drivers(self, query: str) -> List[DriverService]:
        """Search drivers"""
        try:
            data = await self._request('GET', '/drivers/search/', params={'q': query})

            if 'error' in data:
                logger.warning(f"Error searching drivers: {data['error']}")
                return []

            return [self._dict_to_driver(driver_data) for driver_data in data]
        except Exception as e:
            logger.error(f"Error searching drivers: {str(e)}")
            return []

    async def list_drivers(self, filters: Optional[Dict[str, Any]] = None) -> dict:
        """Get drivers list with filters"""
        try:
            params = filters or {}
            data = await self._request('GET', '/drivers/', params=params)

            if 'error' in data:
                logger.warning(f"Error listing drivers: {data['error']}")
                return []

            return data
        except Exception as e:
            logger.error(f"Error listing drivers: {str(e)}")
            return []


    # Car methods
    async def get_car(self, car_id: int) -> Optional[CarService]:
        """Get car by ID"""
        try:
            data = await self._request('GET', f'/cars/{car_id}/')

            if 'error' in data:
                logger.warning(f"Error getting car {car_id}: {data['error']}")
                return None

            return self._dict_to_car(data)
        except Exception as e:
            logger.error(f"Error getting car {car_id}: {str(e)}")
            return None

    async def create_car(self, car_data: Dict[str, Any]) -> Optional[CarService]:
        """Create new car"""
        try:
            data = await self._request('POST', '/cars/', json=car_data)

            if 'error' in data:
                logger.warning(f"Error creating car: {data['error']}")
                return None

            return self._dict_to_car(data)
        except Exception as e:
            logger.error(f"Error creating car: {str(e)}")
            return None

    async def update_car(self, car_id: int, update_data: Dict[str, Any]) -> Optional[CarService]:
        """Update car"""
        try:
            data = await self._request('PATCH', f'/cars/{car_id}/', json=update_data)

            if 'error' in data:
                logger.warning(f"Error updating car {car_id}: {data['error']}")
                return None

            return self._dict_to_car(data)
        except Exception as e:
            logger.error(f"Error updating car {car_id}: {str(e)}")
            return None

    async def get_cars_by_driver(self, driver_id: int) -> List[CarService]:
        """Get cars by driver ID"""
        try:
            data = await self._request('GET', '/cars/by_driver/', params={'driver_id': driver_id})

            if 'error' in data:
                logger.warning(f"Error getting cars by driver {driver_id}: {data['error']}")
                return []

            return [self._dict_to_car(car_data) for car_data in data]
        except Exception as e:
            logger.error(f"Error getting cars by driver {driver_id}: {str(e)}")
            return []

    # Driver Transaction methods
    async def get_transaction(self, transaction_id: int) -> Optional[DriverTransactionService]:
        """Get transaction by ID"""
        try:
            data = await self._request('GET', f'/driver-transactions/{transaction_id}/')

            if 'error' in data:
                logger.warning(f"Error getting transaction {transaction_id}: {data['error']}")
                return None

            return self._dict_to_transaction(data)
        except Exception as e:
            logger.error(f"Error getting transaction {transaction_id}: {str(e)}")
            return None

    async def create_transaction(self, transaction_data: Dict[str, Any]) -> Optional[DriverTransactionService]:
        """Create new transaction"""
        try:
            data = await self._request('POST', '/driver-transactions/', json=transaction_data)

            if 'error' in data:
                logger.warning(f"Error creating transaction: {data['error']}")
                return None

            return self._dict_to_transaction(data)
        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}")
            return None

    async def get_driver_stats(self, driver_id: int) -> Optional[Dict[str, Any]]:
        """Get driver statistics"""
        try:
            data = await self._request('GET', '/driver-transactions/driver_stats/', params={'driver_id': driver_id})

            if 'error' in data:
                logger.warning(f"Error getting driver stats {driver_id}: {data['error']}")
                return None

            return data
        except Exception as e:
            logger.error(f"Error getting driver stats {driver_id}: {str(e)}")
            return None

    async def list_transactions(self, filters: Optional[Dict[str, Any]] = None) -> List[DriverTransactionService]:
        """Get transactions list with filters"""
        try:
            params = filters or {}
            data = await self._request('GET', '/driver-transactions/', params=params)

            if 'error' in data:
                logger.warning(f"Error listing transactions: {data['error']}")
                return []

            return [self._dict_to_transaction(transaction_data) for transaction_data in data.get('results', [])]
        except Exception as e:
            logger.error(f"Error listing transactions: {str(e)}")
            return []

    # Conversion methods
    def _dict_to_driver(self, data: Dict[str, Any]) -> DriverService:
        """Convert dictionary to DriverService object"""
        return DriverService(
            id=data.get('id'),
            telegram_id=data.get('telegram_id'),
            from_location=data.get('from_location', ''),
            to_location=data.get('to_location', ''),
            status=data.get('status', 'active'),
            amount=data.get('amount', 0.0),

        )

    def _dict_to_car(self, data: Dict[str, Any]) -> CarService:
        """Convert dictionary to CarService object"""
        return CarService(
            id=data.get('id'),
            driver_id=data.get('driver'),
            car_number=data.get('car_number', ''),
            car_model=data.get('car_model', ''),
            car_color=data.get('car_color', ''),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def _dict_to_transaction(self, data: Dict[str, Any]) -> DriverTransactionService:
        """Convert dictionary to DriverTransactionService object"""
        return DriverTransactionService(
            id=data.get('id'),
            driver_id=data.get('driver'),
            amount=data.get('amount', 0.0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def driver_to_dict(self, driver: DriverService) -> Dict[str, Any]:
        """Convert DriverService object to dictionary"""
        return asdict(driver)

    def car_to_dict(self, car: CarService) -> Dict[str, Any]:
        """Convert CarService object to dictionary"""
        return asdict(car)

    def transaction_to_dict(self, transaction: DriverTransactionService) -> Dict[str, Any]:
        """Convert DriverTransactionService object to dictionary"""
        return asdict(transaction)

    # Utility methods
    async def driver_exists(self, telegram_id: int) -> bool:
        """Check if driver exists by telegram ID"""
        driver = await self.get_driver_by_telegram_id(telegram_id)
        return driver is not None

    async def is_driver_online(self, driver_id: int) -> bool:
        """Check if driver is active"""
        driver = await self.get_driver(driver_id)
        if driver is None:
            return False
        return driver.status == 'online'

    async def separation_amount(self, telegram_id):
        driver = await self.get_driver_by_telegram_id(telegram_id)
        return self._request(
            "PATCH",
            f"/drivers/{driver.id}/separation_amount",
        )
