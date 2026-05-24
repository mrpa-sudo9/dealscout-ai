
import httpx

from core.config import settings
from database.models import Content
from distribution.base import BasePublisher


class FacebookPublisher(BasePublisher):
    name = "facebook"

    async def publish(self, content: Content) -> str | None:
        if not settings.facebook_page_access_token or not settings.facebook_page_id:
            self.log.warning("Facebook credentials not configured")
            return None

        url = f"https://graph.facebook.com/v19.0/{settings.facebook_page_id}/feed"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data={
                "message": content.body[:5000],
                "access_token": settings.facebook_page_access_token,
            })
            data = resp.json()
            return data.get("id")
