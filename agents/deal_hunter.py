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


MARKETPLACE_MAP = {
    "ebay": Marketplace.EBAY,
    "amazon": Marketplace.AMAZON,
    "aliexpress": Marketplace.ALIEXPRESS,
    "walmart": Marketplace.WALMART,
    "generic": Marketplace.OTHER,
}

NICHE_CATEGORIES = {"fashion", "toys", "sports", "beauty"}

NICHE_KEYWORDS = {
    "fashion": [
        "abbigliamento", "scarpe", "stivali", "sandali", "maglietta", "camicia",
        "pantaloni", "jeans", "giacca", "giacche", "cappotto", "vestito", "abito",
        "gonna", "costume", "borsa", "zaino", "portafoglio", "cintura", "orologio",
        "bracciale", "collana", "anello", "occhiali", "moda", "fashion", "shoes",
        "bag", "tuta", "felpa", "polo", "bermuda", "cappello", "sneaker",
    ],
    "toys": [
        "giocattolo", "giocattoli", "giochi", "gioco", "lego", "barbie", "peluche",
        "action figure", "puzzle", "costruzioni", "macchinina", "trenino", "palla",
        "triciclo", "bicicletta bambino", "monopattino bambino", "tavolo gioco",
        "cucina gioco", "pista", "robot gioco", "toys", "toy",
    ],
    "sports": [
        "sport", "fitness", "palestra", "corsa", "running", "bicicletta", "bici",
        "cyclette", "tapis roulant", "pesi", "manubri", "yoga", "tappetino",
        "scarpe sportive", "pallone", "palla calcio", "racchetta", "casco",
        "protezioni sport", "kayak", "nuoto", "cuffia", "zaino sportivo",
        "sacca sport", "borraccia", "smartwatch sport", "activity tracker",
    ],
    "beauty": [
        "bellezza", "makeup", "make-up", "cosmetico", "cosmetici", "profumo",
        "crema", "siero", "shampoo", "balsamo", "maschera viso", "fondotinta",
        "rossetto", "mascara", "pallet ombretti", "smalto", "struccante",
        "detergente viso", "idratante", "antirughe", "acqua micellare",
        "spazzola capelli", "phon", "arricciacapelli", "rasoio", "depilatore",
        "beauty", "makeup", "cosmetics", "skincare",
    ],
}

CATEGORY_KEYWORD_MAP = {}
for cat, keywords in NICHE_KEYWORDS.items():
    for kw in keywords:
        CATEGORY_KEYWORD_MAP[kw] = cat


def detect_category(item: dict) -> str | None:
    explicit = item.get("category")
    if explicit and explicit in NICHE_CATEGORIES:
        return explicit
    name = (item.get("name") or "").lower()
    for keyword, category in CATEGORY_KEYWORD_MAP.items():
        if keyword in name:
            return category
    return None


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
        tasks.append(scrape_marketplace(Marketplace.OTHER, DealAggregatorScraper()))

        results = await asyncio.gather(*tasks)
        marketplaces = list(self.SCRAPER_MAP.keys()) + [Marketplace.OTHER]

        for marketplace, scraped_products in zip(marketplaces, results):
            for item in scraped_products:
                try:
                    detected = item.get("marketplace", "").lower()
                    mp = MARKETPLACE_MAP.get(detected, marketplace)
                    product_category = detect_category(item)
                    if not product_category:
                        continue

                    product = await product_repo.get_or_create(
                        marketplace=mp,
                        sku=item.get("sku", str(hash(item.get("url", "")))),
                        defaults={
                            "name": item["name"],
                            "marketplace_url": item["url"],
                            "image_url": item.get("image_url"),
                            "description": item.get("description"),
                            "key_features": item.get("features"),
                            "category": product_category,
                            "currency": item.get("currency", "EUR"),
                        },
                    )

                    current_price = Decimal(str(item["price"]))
                    await price_repo.add(product.id, current_price, product.currency, mp.value)

                    record_count = await price_repo.count_recent(product.id)
                    avg_price = await price_repo.get_avg_price_30d(product.id)

                    if avg_price is not None:
                        discount = float((1 - current_price / avg_price) * 100)
                    elif mp == Marketplace.EBAY:
                        avg_price = current_price * Decimal("1.35")
                        discount = 25.0
                    else:
                        discount = 0.0

                    if record_count < 3:
                        discount = max(discount, 25.0)

                    if discount < settings.min_discount_percent:
                        continue

                    already_exists = await deal_repo.exists_recent(product.id, settings.max_deal_age_days)
                    if already_exists:
                        continue

                    await deal_repo.create(
                        product_id=product.id,
                        current_price=current_price,
                        avg_market_price=avg_price,
                        discount_percent=round(discount, 2),
                        status=DealStatus.PENDING,
                    )
                    self.log.info(f"New deal: [{product_category}] {product.name} - {discount:.1f}% off ({current_price}€)")

                except Exception as e:
                    self.log.error(f"Failed to process product {item.get('name', 'unknown')}: {e}")
