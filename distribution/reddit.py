from base64 import b64encode

import httpx

from core.config import settings
from database.models import Content
from distribution.base import BasePublisher


class RedditPublisher(BasePublisher):
    name = "reddit"

    async def _get_token(self) -> str | None:
        auth = b64encode(f"{settings.reddit_client_id}:{settings.reddit_client_secret}".encode()).decode()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://www.reddit.com/api/v1/access_token",
                headers={"Authorization": f"Basic {auth}", "User-Agent": settings.reddit_user_agent},
                data={"grant_type": "client_credentials"},
            )
            data = resp.json()
            return data.get("access_token")

    async def publish(self, content: Content) -> str | None:
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            self.log.warning("Reddit credentials not configured")
            return None

        token = await self._get_token()
        if not token:
            return None

        title = content.body[:80].split("\n")[0] if content.body else "Deal Alert"
        text = content.body[:5000]

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth.reddit.com/api/submit",
                headers={"Authorization": f"Bearer {token}", "User-Agent": settings.reddit_user_agent},
                data={
                    "sr": "shoppingdeals",
                    "title": title,
                    "kind": "self",
                    "text": text,
                    "resubmit": True,
                },
            )
            data = resp.json()
            return data.get("jump", {}).get("id", str(resp.status_code))
