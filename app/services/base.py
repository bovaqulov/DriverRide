from typing import Optional, Dict, Any

import aiohttp

from app.core import logger
from app.core.config import settings
from .http_client import GlobalHTTPClient


class BaseService:
    def __init__(self):
        self.base_url = f"{settings.API_HOST}/{settings.API_VERSION}"
        self.token = settings.AUTH_TOKEN
        self.http_client = GlobalHTTPClient()

    def _headers(self, extra: Optional[Dict] = None) -> Dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        if extra:
            headers.update(extra)
        return headers

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        kwargs["headers"] = self._headers(kwargs.pop("headers", None))

        try:
            async with self.http_client.request(method, url, **kwargs) as response:
                if response.status == 204:
                    return {}

                content_type = response.headers.get("Content-Type", "").lower()
                if "text/html" in content_type:
                    text = await response.text()
                    logger.warning(f"HTML response for {url}: {text[:200]}")
                    if response.status == 404:
                        return {"detail": "Not found"}
                    raise Exception(f"Unexpected HTML: {response.status}")

                try:
                    data = await response.json()
                except aiohttp.ContentTypeError:
                    text = await response.text()
                    logger.warning(f"Non-JSON response for {url}: {text[:200]}")
                    raise Exception(f"Non-JSON response: {text[:100]}")

                if not 200 <= response.status < 300:
                    error_msg = (
                        data.get("detail") or data.get("error") or f"HTTP {response.status}"
                    )
                    logger.error(f"API error {response.status} from {url}: {error_msg}")
                    raise Exception(f"API Error: {error_msg}")

                return data

        except aiohttp.ClientError as e:
            logger.error(f"Network error for {url}: {e}")
            raise Exception(f"Network error: {e}")
        except Exception:
            raise
