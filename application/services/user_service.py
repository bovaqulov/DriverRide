# application/services/user_service.py

from typing import Optional, Dict, Any
from dataclasses import asdict
from ..core.log import logger
from ..services.base import BaseService
from ..services.types import UserService


class TelegramUser(BaseService):
    async def get_user(self, telegram_id: int) -> Optional[UserService]:
        """Get user by telegram ID"""
        try:
            data = await self._request('GET', f'/clients/by-telegram-id/{telegram_id}/')

            # Agar foydalanuvchi topilmasa
            if 'detail' in data and data['detail'] == 'Not found':
                logger.info(f"User {telegram_id} not found")
                return None
            if 'error' in data:
                logger.warning(f"Error in response for user {telegram_id}: {data['error']}")
                return None

            return self._dict_to_user(data)
        except Exception as e:
            logger.error(f"Error getting user {telegram_id}: {str(e)}")
            return None

    async def create_user(self, user_data: Dict[str, Any]) -> Optional[UserService]:
        """Create new user"""
        try:
            data = await self._request('POST', '/clients/', json=user_data)

            if 'error' in data:
                logger.warning(f"Error creating user: {data['error']}")
                return None

            return self._dict_to_user(data)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None

    async def update_user(self, telegram_id: int, update_data: Dict[str, Any]) -> Optional[UserService]:
        """Update user"""
        try:
            data = await self._request('PATCH', f'/clients/{telegram_id}/', json=update_data)

            if 'error' in data:
                logger.warning(f"Error updating user {telegram_id}: {data['error']}")
                return None

            return self._dict_to_user(data)
        except Exception as e:
            logger.error(f"Error updating user {telegram_id}: {str(e)}")
            return None

    async def ban_user(self, telegram_id: int) -> Optional[UserService]:
        """Ban user"""
        try:
            data = await self._request('POST', f'/clients/{telegram_id}/ban/')

            if 'error' in data:
                logger.warning(f"Error banning user {telegram_id}: {data['error']}")
                return None

            return self._dict_to_user(data)
        except Exception as e:
            logger.error(f"Error banning user {telegram_id}: {str(e)}")
            return None

    async def unban_user(self, telegram_id: int) -> Optional[UserService]:
        """Unban user"""
        try:
            data = await self._request('POST', f'/clients/{telegram_id}/unban/')

            if 'error' in data:
                logger.warning(f"Error unbanning user {telegram_id}: {data['error']}")
                return None

            return self._dict_to_user(data)
        except Exception as e:
            logger.error(f"Error unbanning user {telegram_id}: {str(e)}")
            return None

    async def increment_rides(self, telegram_id: int) -> Optional[UserService]:
        """Increment user rides count"""
        try:
            data = await self._request('POST', f'/clients/{telegram_id}/increment_rides/')

            if 'error' in data:
                logger.warning(f"Error incrementing rides for user {telegram_id}: {data['error']}")
                return None

            return self._dict_to_user(data)
        except Exception as e:
            logger.error(f"Error incrementing rides for user {telegram_id}: {str(e)}")
            return None

    def _dict_to_user(self, data: Dict[str, Any]) -> UserService:
        """Convert dictionary to UserService object"""
        return UserService(
            telegram_id=data.get('telegram_id'),
            username=data.get('username'),
            full_name=data.get('full_name', ''),
            language=data.get('language', 'uz'),
            is_active=data.get('is_active', True),
            is_banned=data.get('is_banned', False),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def user_to_dict(self, user: UserService) -> Dict[str, Any]:
        """Convert UserService object to dictionary"""
        return asdict(user)


    async def get_lang(self, telegram_id: int) -> Optional[UserService]:
        user =  await self.get_user(telegram_id)
        return user.language

    async def is_ban_user(self, telegram_id: int) -> bool:
        """Check if user is banned."""
        user = await self.get_user(telegram_id)
        if user is None:
            return False
        return user.is_banned


    async def user_exists(self, telegram_id: int) -> bool:
        """Check if user exists"""
        user = await self.get_user(telegram_id)
        return user is not None