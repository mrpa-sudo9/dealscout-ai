import asyncio
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent
from core.config import settings
from database.models import DealStatus, Marketplace
from database.repositories import DealRepository, PriceRecordRepository, ProductRepository
from scrapers.aliexpress import AliExpressScraper
from scrapers.amazon import AmazonScraper
from scrapers.base import BaseScraper
from scrapers.decathlon import DecathlonScraper
from scrapers.ebay import EbayScraper
from scrapers.etsy import EtsyScraper
from scrapers.fnac import FnacScraper
from scrapers.manomano import ManoManoScraper
from scrapers.mediamarkt import MediaMarktScraper
from scrapers.rakuten import RakutenScraper
from scrapers.vinted import VintedScraper
from scrapers.walmart import WalmartScraper
from scrapers.zalando import ZalandoScraper
from utils.price_utils import is_significant_discount


class DealHunter(BaseAgent):
    name = "DealHunter"

    SCRAPER_MAP: dict[Marketplace, type[BaseScraper]] = {
        Marketplace.AMAZON: AmazonScraper,
        Marketplace.EBAY: EbayScraper,
        Marketplace.ETSY: EtsyScraper,
        Marketplace.ALIEXPRESS: AliExpressScraper,
        Marketplace.DECATHLON: DecathlonScraper,
        Marketplace.ZALANDO: ZalandoScraper,
        Marketplace.MEDIAMARKT: MediaMarktScraper,
        Marketplace.FNAC: FnacScraper,
        Marketplace.VINTED: VintedScraper,
        Marketplace.MANOMANO: ManoManoScraper,
        Marketplace.WALMART: WalmartScraper,
        Marketplace.RAKUTEN: RakutenScraper,
    }

    async def execute(self, session: AsyncSession):
        product_repo = ProductRepository(session)
        price_repo = PriceRecordRepository(session)
        deal_repo = DealRepository(session)

        semaphore = asyncio.Semaphore(settings.max_concurrent_scrapes)

        async def scrape_marketplace(marketplace: Marketplace):
            scraper_class = self.SCRAPER_MAP.get(marketplace)
            if not scraper_class:
                self.log.warning(f"No scraper for {marketplace}")
                return []

            async with semaphore:
                try:
                    scraper = scraper_class()
                    products = await scraper.scrape()
                    self.log.info(f"[{marketplace}] Scraped {len(products)} products")
                    return products
                except Exception as e:
                    self.log.error(f"[{marketplace}] Scrape failed: {e}")
                    return []

        tasks = [scrape_marketplace(mp) for mp in self.SCRAPER_MAP]
        results = await asyncio.gather(*tasks)

        for marketplace, scraped_products in zip(self.SCRAPER_MAP.keys(), results):
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
