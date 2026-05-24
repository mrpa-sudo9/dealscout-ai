import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent
from content.generator import ContentGenerator
from database.models import DealStatus
from database.repositories import ContentRepository, DealRepository


class ContentCreator(BaseAgent):
    name = "ContentCreator"

    async def execute(self, session: AsyncSession):
        deal_repo = DealRepository(session)
        content_repo = ContentRepository(session)
        generator = ContentGenerator()

        ready_deals = await deal_repo.get_affiliate_ready(limit=50)
        self.log.info(f"Creating content for {len(ready_deals)} deals")

        gemini_exhausted = False
        for idx, deal in enumerate(ready_deals):
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

                use_llm = not gemini_exhausted and idx < 30
                if use_llm:
                    await asyncio.sleep(1.5)
                    contents = await generator.generate_all(content_payload)
                    tel_content = contents.get(ChannelType.TELEGRAM, "")
                    if "🏷️" in tel_content and "💰" in tel_content:
                        gemini_exhausted = True
                        self.log.info("Gemini quota exhausted, switching to fallback for remaining deals")
                else:
                    contents = generator._fallback_templates(content_payload)

                for channel_type, text in contents.items():
                    await content_repo.create(
                        deal_id=deal.id,
                        channel=channel_type,
                        body=text,
                    )

                await deal_repo.update_status(deal.id, DealStatus.CONTENT_READY)
                self.log.info(f"Content created for deal {deal.id} ({'LLM' if use_llm else 'fallback'})")

            except Exception as e:
                self.log.error(f"Content generation failed for deal {deal.id}: {e}")
