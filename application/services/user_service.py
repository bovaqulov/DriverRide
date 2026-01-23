# application/services/user_service.py

from typing import Optional, Dict, Any


from pydantic import BaseModel

from ..core.log import logger
from ..services.base import BaseService

class UserService(BaseModel):
    user_id: int
    telegram_id: int
    full_name: str
    language: str
    is_banned: bool
    username: Optional[str] = None


class TelegramUserServiceAPI(BaseService):
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


    def _dict_to_user(self, data: Dict[str, Any]) -> UserService:
        """Convert dictionary to UserService object"""
        return UserService(**data)


    async def get_lang(self, telegram_id: int) -> Optional[UserService]:
        user =  await self.get_user(telegram_id)
        return user.language

    async def is_ban_user(self, telegram_id: int) -> bool:
        """Check if user is banned."""
        user = await self.get_user(telegram_id)
        if user is None:
            return False
        return user.is_banned