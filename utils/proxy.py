import random

from core.config import settings


class ProxyManager:
    def __init__(self):
        self.proxies: list[str] = []
        if settings.proxy_list:
            self.proxies = [p.strip() for p in settings.proxy_list.split(",") if p.strip()]

    def get_random(self) -> str | None:
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    def get_httpx_proxy(self) -> str | None:
        proxy = self.get_random()
        if proxy:
            return f"http://{proxy}"
        return None


proxy_manager = ProxyManager()
