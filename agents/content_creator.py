import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent
from content.generator import ContentGenerator
from database.models import ChannelType, DealStatus
from database.repositories import ContentRepository, DealRepository


class ContentCreator(BaseAgent):
    name = "ContentCreator"

    async def execute(self, session: AsyncSession):
        deal_repo = DealRepository(session)
        content_repo = ContentRepository(session)
        generator = ContentGenerator()

        ready_deals = await deal_repo.get_affiliate_ready(limit=50)
        self.log.info(f"Creating content for {len(ready_deals)} deals")

        for deal in ready_deals:
            try:
                product = deal.product
                content_payload = {
                    "product_name": product.name,
                    "current_price": float(deal.current_price),
                    "avg_price": float(deal.avg_market_price),
                    "discount": round(deal.discount_percent),
                    "marketplace": product.marketplace.value,
                    "description": product.description or "",
                    "key_features": product.key_features or {},
                    "affiliate_link": deal.affiliate_link or product.marketplace_url,
                    "image_url": product.image_url or "",
                }

                await asyncio.sleep(1.5)
                contents = await generator.generate_all(content_payload)

                for channel_type, text in contents.items():
                    await content_repo.create(
                        deal_id=deal.id,
                        channel=channel_type,
                        body=text,
                    )

                await deal_repo.update_status(deal.id, DealStatus.CONTENT_READY)
                self.log.info(f"Content created for deal {deal.id} (LLM)")

            except Exception as e:
                self.log.error(f"Content generation failed for deal {deal.id}: {e}")
                try:
                    contents = generator._fallback_templates(content_payload)
                    for channel_type, text in contents.items():
                        await content_repo.create(
                            deal_id=deal.id,
                            channel=channel_type,
                            body=text,
                        )
                    await deal_repo.update_status(deal.id, DealStatus.CONTENT_READY)
                    self.log.info(f"Fallback content created for deal {deal.id}")
                except Exception as e2:
                    self.log.error(f"Fallback also failed for deal {deal.id}: {e2}")
                    await deal_repo.update_status(deal.id, DealStatus.FAILED)
