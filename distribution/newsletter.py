
import httpx

from core.config import settings
from database.models import Content
from distribution.base import BasePublisher


class NewsletterPublisher(BasePublisher):
    name = "newsletter"

    async def publish(self, content: Content) -> str | None:
        if not settings.mailchimp_api_key or not settings.mailchimp_list_id:
            self.log.warning("Mailchimp credentials not configured")
            return None

        body = content.body
        subject = "Nuova offerta"
        if body and "\n" in body:
            first_line = body.split("\n")[0]
            if first_line.startswith("Oggetto:"):
                subject = first_line.replace("Oggetto:", "").strip()
                body = "\n".join(body.split("\n")[1:])

        dc = settings.mailchimp_api_key.split("-")[-1]
        url = f"https://{dc}.api.mailchimp.com/3.0/campaigns"

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, auth=("apikey", settings.mailchimp_api_key), json={
                "type": "regular",
                "recipients": {"list_id": settings.mailchimp_list_id},
                "settings": {
                    "subject_line": subject,
                    "title": f"DealScout - {subject}",
                    "from_name": "DealScout AI",
                    "reply_to": "dealscout@example.com",
                },
            })
            campaign = resp.json()
            campaign_id = campaign.get("id")
            if not campaign_id:
                return None

            await client.put(
                f"https://{dc}.api.mailchimp.com/3.0/campaigns/{campaign_id}/content",
                auth=("apikey", settings.mailchimp_api_key),
                json={"html": f"<div style='font-family:sans-serif;max-width:600px;margin:0 auto;'>{body}</div>"},
            )

            await client.post(
                f"https://{dc}.api.mailchimp.com/3.0/campaigns/{campaign_id}/actions/send",
                auth=("apikey", settings.mailchimp_api_key),
            )

            return campaign_id
