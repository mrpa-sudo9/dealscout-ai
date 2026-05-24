
import httpx

from core.config import settings
from database.models import Content
from distribution.base import BasePublisher


class PinterestPublisher(BasePublisher):
    name = "pinterest"

    async def publish(self, content: Content) -> str | None:
        if not settings.pinterest_access_token or not settings.pinterest_board_id:
            self.log.warning("Pinterest credentials not configured")
            return None

        url = "https://api.pinterest.com/v5/pins"
        deal = content.deal
        image_url = deal.product.image_url if deal else None
        if not image_url:
            self.log.warning("No image URL for Pinterest pin")
            return None

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers={
                "Authorization": f"Bearer {settings.pinterest_access_token}",
            }, json={
                "board_id": settings.pinterest_board_id,
                "media_source": {"source_type": "image_url", "url": image_url},
                "title": content.body[:100] if content.body else "Deal Alert",
                "description": content.body[:500],
                "link": deal.product.marketplace_url if deal else "",
            })
            data = resp.json()
            return data.get("id")
