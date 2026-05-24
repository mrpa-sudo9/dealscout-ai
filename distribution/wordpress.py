from base64 import b64encode

import httpx

from core.config import settings
from database.models import Content
from distribution.base import BasePublisher


class WordPressPublisher(BasePublisher):
    name = "wordpress"

    async def publish(self, content: Content) -> str | None:
        if not all([settings.wordpress_url, settings.wordpress_username, settings.wordpress_app_password]):
            self.log.warning("WordPress credentials not configured")
            return None

        body = content.body
        title = content.seo_title or "Nuova offerta"
        meta = content.seo_description or ""

        lines = body.split("\n")
        for line in lines:
            if line.startswith("Titolo:"):
                title = line.replace("Titolo:", "").strip()
            elif line.startswith("Meta:"):
                meta = line.replace("Meta:", "").strip()

        auth_str = b64encode(f"{settings.wordpress_username}:{settings.wordpress_app_password}".encode()).decode()
        url = f"{settings.wordpress_url.rstrip('/')}/wp-json/wp/v2/posts"

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers={
                "Authorization": f"Basic {auth_str}",
            }, json={
                "title": title,
                "content": body,
                "status": "publish",
                "meta": {"_yoast_wpseo_metadesc": meta} if meta else {},
            })
            data = resp.json()
            return str(data.get("id", ""))
