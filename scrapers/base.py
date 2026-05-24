from abc import ABC, abstractmethod
from typing import Any

import httpx

from core.config import settings
from utils.logger import log
from utils.proxy import proxy_manager


class BaseScraper(ABC):
    marketplace: str = "base"
    base_url: str = ""

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=settings.request_timeout,
            follow_redirects=True,
        )
        self.log = log

    @abstractmethod
    async def scrape(self) -> list[dict[str, Any]]:
        ...

    async def _fetch(self, url: str, params: dict | None = None) -> httpx.Response:
        proxy = proxy_manager.get_httpx_proxy()
        client_kwargs = {"proxy": proxy} if proxy else {}
        async with httpx.AsyncClient(**client_kwargs, timeout=settings.request_timeout) as client:
            return await client.get(url, params=params)

    async def close(self):
        await self.client.aclose()
