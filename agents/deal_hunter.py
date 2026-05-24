import asyncio
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent
from core.config import settings
from database.models import DealStatus, Marketplace
from database.repositories import DealRepository, PriceRecordRepository, ProductRepository
from scrapers.amazon import AmazonScraper
from scrapers.base import BaseScraper
from scrapers.deal_aggregator import DealAggregatorScraper
from scrapers.ebay import EbayScraper
from utils.price_utils import is_significant_discount


class DealHunter(BaseAgent):
    name = "DealHunter"

    SCRAPER_MAP: dict[Marketplace, type[BaseScraper]] = {
        Marketplace.AMAZON: AmazonScraper,
        Marketplace.EBAY: EbayScraper,
    }

    async def execute(self, session: AsyncSession):
        product_repo = ProductRepository(session)
        price_repo = PriceRecordRepository(session)
        deal_repo = DealRepository(session)

        semaphore = asyncio.Semaphore(settings.max_concurrent_scrapes)

        async def scrape_marketplace(marketplace: Marketplace, scraper: BaseScraper):
            async with semaphore:
                try:
                    products = await scraper.scrape()
                    self.log.info(f"[{marketplace}] Scraped {len(products)} products")
                    return products
                except Exception as e:
                    self.log.error(f"[{marketplace}] Scrape failed: {e}")
                    return []

        tasks = []
        for mp, cls in self.SCRAPER_MAP.items():
            tasks.append(scrape_marketplace(mp, cls()))

        tasks.append(scrape_marketplace(Marketplace.AMAZON, DealAggregatorScraper()))

        results = await asyncio.gather(*tasks)

        marketplaces = list(self.SCRAPER_MAP.keys()) + [Marketplace.AMAZON]

        for marketplace, scraped_products in zip(marketplaces, results):
            for item in scraped_products:
                try:
                    product = await product_repo.get_or_create(
                        marketplace=marketplace,
                        sku=item.get("sku", item.get("url", "")),
                        defaults={
                            "name": item["name"],
                            "marketplace_url": item["url"],
                            "image_url": item.get("image_url"),
                            "description": item.get("description"),
                            "key_features": item.get("features"),
                            "category": item.get("category"),
                            "currency": item.get("currency", "EUR"),
                        },
                    )

                    current_price = Decimal(str(item["price"]))
                    await price_repo.add(product.id, current_price, product.currency, marketplace.value)

                    avg_price = await price_repo.get_avg_price_30d(product.id)
                    if avg_price is None:
                        avg_price = current_price

                    if not is_significant_discount(current_price, avg_price, settings.min_discount_percent):
                        continue

                    already_exists = await deal_repo.exists_recent(product.id, settings.max_deal_age_days)
                    if already_exists:
                        continue

                    discount = float((1 - current_price / avg_price) * 100)
                    await deal_repo.create(
                        product_id=product.id,
                        current_price=current_price,
                        avg_market_price=avg_price,
                        discount_percent=round(discount, 2),
                        status=DealStatus.PENDING,
                    )
                    self.log.info(f"New deal: {product.name} - {discount:.1f}% off ({current_price}€ vs {avg_price}€)")

                except Exception as e:
                    self.log.error(f"Failed to process product {item.get('name', 'unknown')}: {e}")
