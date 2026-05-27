from sqlalchemy import not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent
from content.generator import ContentGenerator
from database.models import ChannelType, Deal, DealStatus, PriceRecord, Product
from database.repositories import ContentRepository, DealRepository, PriceRecordRepository, ProductRepository


class ProductSpotlighter(BaseAgent):
    name = "ProductSpotlighter"

    async def execute(self, session: AsyncSession):
        product_repo = ProductRepository(session)
        deal_repo = DealRepository(session)
        content_repo = ContentRepository(session)
        price_repo = PriceRecordRepository(session)
        generator = ContentGenerator()

        products_with_recent_deals = select(Deal.product_id).where(
            Deal.created_at.isnot(None)
        )
        result = await session.execute(
            select(Product).where(not_(Product.id.in_(products_with_recent_deals)))
        )
        all_products: list[Product] = list(result.scalars().all())

        self.log.info(f"Found {len(all_products)} products without deals — creating spotlights")

        MAX_SPOTLIGHTS = 50
        count = 0

        for product in all_products:
            if count >= MAX_SPOTLIGHTS:
                break

            price_result = await session.execute(
                select(PriceRecord).where(PriceRecord.product_id == product.id).order_by(PriceRecord.recorded_at.desc()).limit(1)
            )
            latest_price = price_result.scalar_one_or_none()
            if not latest_price or latest_price.price <= 0:
                continue

            current_price = latest_price.price

            deal = Deal(
                product_id=product.id,
                current_price=current_price,
                avg_market_price=current_price,
                discount_percent=0.0,
                status=DealStatus.SPOTLIGHT,
                affiliate_link=product.marketplace_url,
            )
            session.add(deal)
            await session.flush()

            payload = {
                "product_name": product.name,
                "current_price": float(current_price),
                "avg_price": float(current_price),
                "discount": 0,
                "marketplace": product.marketplace.value,
                "description": product.description or "",
                "key_features": product.key_features or {},
                "affiliate_link": deal.affiliate_link or product.marketplace_url,
                "image_url": product.image_url or "",
            }

            contents = generator._fallback_templates(payload)

            for channel_type, text in contents.items():
                if channel_type in (ChannelType.TELEGRAM,):
                    await content_repo.create(deal_id=deal.id, channel=channel_type, body=text)

            deal.status = DealStatus.CONTENT_READY
            self.log.info(f"[{count+1}/{MAX_SPOTLIGHTS}] Spotlight: {product.name[:50]} ({product.category}) — {current_price}€")
            count += 1

        self.log.info(f"Created {count} spotlight deals")