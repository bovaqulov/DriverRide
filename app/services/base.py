from typing import Optional

import aiohttp

from app.core import logger
from app.core.config import settings


class BaseService:
    def __init__(self):
        self.base_url = f'{settings.MAIN_URL}/{settings.API_VERSION}'
        self.token = settings.AUTH_TOKEN
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()

    async def _ensure_session(self) -> None:
        if self.session is None or self.session.closed:
            headers = {'Content-Type': 'application/json'}
            if self.token:
                headers['Authorization'] = f'Token {self.token}'
            self.session = aiohttp.ClientSession(headers=headers)

    async def close_session(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        await self._ensure_session()
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 204:
                    return {}

                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type:
                    text = await response.text()
                    logger.warning(f"HTML response for {url}: {text[:200]}")
                    if response.status == 404:
                        return {'detail': 'Not found'}
                    raise Exception(f"Unexpected HTML response: {response.status}")

                try:
                    data = await response.json()
                except Exception:
                    text = await response.text()
                    logger.warning(f"Non-JSON response for {url}: {text[:200]}")
                    raise Exception(f"Non-JSON response: {text[:100]}")

                if not 200 <= response.status < 300:
                    error_msg = data.get('detail') or data.get('error') or f'HTTP {response.status}'
                    raise Exception(f"API Error: {error_msg}")

                return data

        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {e}")
