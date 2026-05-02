from typing import Optional

from pydantic import BaseModel

from ..core.log import logger
from ..services.base import BaseService


class UserModel(BaseModel):
    user_id: int
    telegram_id: int
    full_name: str
    language: str
    is_banned: bool
    username: Optional[str] = None


class TelegramUserServiceAPI(BaseService):
    async def get_user(self, telegram_id: int) -> Optional[UserModel]:
        try:
            data = await self._request('GET', f'/clients/by-telegram-id/{telegram_id}/')
            if data.get('detail') == 'Not found' or 'error' in data:
                return None
            return UserModel(**data)
        except Exception as e:
            logger.error(f"get_user({telegram_id}): {e}")
            return None

    async def create_user(self, user_data: dict) -> Optional[UserModel]:
        try:
            data = await self._request('POST', '/clients/', json=user_data)
            if 'error' in data:
                return None
            return UserModel(**data)
        except Exception as e:
            logger.error(f"create_user: {e}")
            return None

    async def get_lang(self, telegram_id: int) -> Optional[str]:
        user = await self.get_user(telegram_id)
        return user.language if user else None

    async def is_ban_user(self, telegram_id: int) -> bool:
        user = await self.get_user(telegram_id)
        return user.is_banned if user else False


user_api = TelegramUserServiceAPI()
