import re
from typing import Any

from scrapers.base import BaseScraper


AMAZON_CATEGORIES: dict[str, str] = {
    "fashion": "/gp/bestsellers/fashion",
    "toys": "/gp/bestsellers/toys",
    "sports": "/gp/bestsellers/sports",
    "beauty": "/gp/bestsellers/beauty",
}


class AmazonScraper(BaseScraper):
    marketplace = "amazon"
    base_url = "https://www.amazon.it"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        seen_asins = set()

        for category_name, path in AMAZON_CATEGORIES.items():
            url = f"{self.base_url}{path}"
            try:
                soup = await self._fetch_soup(url)
                for item in soup.select("[data-asin]"):
                    asin = item.get("data-asin", "").strip()
                    if not asin or asin in seen_asins:
                        continue
                    seen_asins.add(asin)

                    name_el = item.select_one("[class*=truncate]") or item.select_one("h2")
                    price_el = item.select_one("[class*=price]")
                    link_el = item.select_one("a[href*='/dp/']")

                    if not name_el:
                        continue
                    name = name_el.get_text(strip=True)[:500]
                    price_text = ""
                    if price_el:
                        price_text = re.sub(r"[^\d.,]", "", price_el.get_text(strip=True))

                    if not name:
                        continue

                    products.append({
                        "name": name,
                        "price": float(price_text.replace(",", ".")) if price_text else 0.0,
                        "url": f"{self.base_url}/dp/{asin}",
                        "sku": asin,
                        "currency": "EUR",
                        "marketplace": "amazon",
                        "category": category_name,
                    })
            except Exception as e:
                self.log.warning(f"Amazon scrape failed for {url}: {e}")

        self.log.info(f"[Amazon] Scraped {len(products)} products across {len(AMAZON_CATEGORIES)} categories")
        return products
