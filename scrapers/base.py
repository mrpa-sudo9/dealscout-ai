from abc import ABC, abstractmethod
from typing import Any

import httpx

from core.config import settings
from utils.logger import log
from utils.proxy import proxy_manager

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
]


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

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": USER_AGENTS[id(self) % len(USER_AGENTS)],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def _fetch(self, url: str, params: dict | None = None) -> httpx.Response:
        proxy = proxy_manager.get_httpx_proxy()
        client_kwargs = {"proxy": proxy} if proxy else {}
        async with httpx.AsyncClient(**client_kwargs, timeout=settings.request_timeout, headers=self._headers()) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp

    async def _fetch_soup(self, url: str, params: dict | None = None) -> Any:
        from bs4 import BeautifulSoup
        resp = await self._fetch(url, params)
        return BeautifulSoup(resp.text, "lxml")

    async def close(self):
        await self.client.aclose()
