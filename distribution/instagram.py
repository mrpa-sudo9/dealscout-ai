
from core.config import settings
from database.models import Content
from distribution.base import BasePublisher


class InstagramPublisher(BasePublisher):
    name = "instagram"

    async def publish(self, content: Content) -> str | None:
        if not settings.instagram_username or not settings.instagram_password:
            self.log.warning("Instagram credentials not configured")
            return None

        try:
            from instagrapi import Client
            cl = Client()
            cl.login(settings.instagram_username, settings.instagram_password)
            result = cl.photo_upload_to_story(content.body[:2200])
            return str(result.pk)
        except ImportError:
            self.log.error("instagrapi not installed. Install with: pip install instagrapi")
            return None
        except Exception as e:
            self.log.error(f"Instagram publish failed: {e}")
            return None
