"""
Yagona global HTTP client — resurs sizdirgichlarini oldini oladi.
"""
import aiohttp
from typing import Optional
from contextlib import asynccontextmanager


class GlobalHTTPClient:
    _instance: Optional["GlobalHTTPClient"] = None
    _session: Optional[aiohttp.ClientSession] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=20,
                force_close=False,
                enable_cleanup_closed=True,
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={"Content-Type": "application/json"},
            )
        return self._session

    @asynccontextmanager
    async def request(self, method: str, url: str, **kwargs):
        session = await self.get_session()
        async with session.request(method, url, **kwargs) as response:
            yield response

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
