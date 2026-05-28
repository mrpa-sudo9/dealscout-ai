import re
from typing import Any

from scrapers.base import BaseScraper


AMAZON_CATEGORIES: dict[str, dict[str, str]] = {
    "fashion": {
        "bestsellers": "/gp/bestsellers/fashion",
        "new_releases": "/gp/new-releases/fashion",
        "clothing": "/s?i=fashion&rh=n:409566031",
        "shoes": "/s?i=shoes",
        "watches": "/s?i=watches",
    },
    "toys": {
        "bestsellers": "/gp/bestsellers/toys",
        "new_releases": "/gp/new-releases/toys",
        "games": "/s?i=toys&rh=n:302778031",
    },
    "sports": {
        "bestsellers": "/gp/bestsellers/sports",
        "new_releases": "/gp/new-releases/sports",
        "fitness": "/s?i=sports&rh=n:524036031",
    },
    "beauty": {
        "bestsellers": "/gp/bestsellers/beauty",
        "new_releases": "/gp/new-releases/beauty",
    },
    "home_kitchen": {
        "bestsellers": "/gp/bestsellers/kitchen",
        "new_releases": "/gp/new-releases/kitchen",
        "home": "/s?i=kitchen&rh=n:316764031",
    },
    "tech_accessories": {
        "bestsellers": "/gp/bestsellers/electronics",
        "new_releases": "/gp/new-releases/electronics",
        "accessories": "/s?i=electronics&rh=n:412587031",
    },
    "pet_supplies": {
        "bestsellers": "/gp/bestsellers/pet-supplies",
        "new_releases": "/gp/new-releases/pet-supplies",
    },
    "health_wellness": {
        "bestsellers": "/gp/bestsellers/hpc",
        "new_releases": "/gp/new-releases/hpc",
    },
    "electronics": {
        "bestsellers": "/gp/bestsellers/electronics",
        "new_releases": "/gp/new-releases/electronics",
        "smartphones": "/gp/bestsellers/electronics/2311887031",
        "tablets": "/gp/bestsellers/electronics/462427031",
        "headphones": "/gp/bestsellers/electronics/523960031",
        "smartwatches": "/gp/bestsellers/electronics/462752031",
        "tvs": "/gp/bestsellers/electronics/13735011",
        "cameras": "/gp/bestsellers/electronics/412589031",
        "laptop_media": "/s?i=electronics&rh=n:412587031,p_36:100-300&s=exact-aware-popularity-rank",
        "smartphone_alta": "/s?i=electronics&rh=n:2311887031,p_36:300-600&s=exact-aware-popularity-rank",
        "headphones_elite": "/s?i=electronics&rh=n:523960031,p_36:1000-&s=exact-aware-popularity-rank",
    },
}


class AmazonScraper(BaseScraper):
    marketplace = "amazon"
    base_url = "https://www.amazon.it"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        seen_asins = set()

        for category_name, paths in AMAZON_CATEGORIES.items():
            for sub_type, path in paths.items():
                url = f"{self.base_url}{path}"
                try:
                    soup = await self._fetch_soup(url)
                    count = 0
                    for item in soup.select("[data-asin]"):
                        asin = item.get("data-asin", "").strip()
                        if not asin or asin in seen_asins or len(asin) != 10:
                            continue
                        seen_asins.add(asin)

                        name_el = (
                            item.select_one("span[class*='truncate']")
                            or item.select_one("h2 a")
                            or item.select_one("span.a-size-base-plus")
                            or item.select_one("span.a-size-medium")
                            or item.select_one("img[alt]")
                        )
                        name = name_el.get("alt") if name_el and name_el.name == "img" else (name_el.get_text(strip=True) if name_el else "")
                        if not name or len(name) < 5:
                            continue

                        price_el = (
                            item.select_one(".a-price .a-offscreen")
                            or item.select_one(".a-price-whole")
                            or item.select_one("[class*=price] span")
                        )
                        price_text = ""
                        if price_el:
                            price_text = re.sub(r"[^\d.,]", "", price_el.get_text(strip=True))
                        price = float(price_text.replace(",", ".")) if price_text else 0.0

                        if price == 0:
                            continue

                        image_el = item.select_one("img[src*='images']")
                        image_url = image_el.get("src") if image_el else None

                        products.append({
                            "name": name[:500],
                            "price": price,
                            "url": f"{self.base_url}/dp/{asin}",
                            "sku": asin,
                            "currency": "EUR",
                            "marketplace": "amazon",
                            "category": category_name,
                            "image_url": image_url,
                        })
                        count += 1

                    self.log.info(f"[Amazon] {category_name}/{sub_type}: {count} products")
                except Exception as e:
                    self.log.warning(f"Amazon scrape failed for {url}: {e}")

        self.log.info(f"[Amazon] Scraped {len(products)} unique products across {sum(len(v) for v in AMAZON_CATEGORIES.values())} pages")
        return products
