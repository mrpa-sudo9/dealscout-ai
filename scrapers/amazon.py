import re
from typing import Any

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper


class AmazonScraper(BaseScraper):
    marketplace = "amazon"
    base_url = "https://www.amazon.it"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        urls = [
            f"{self.base_url}/gp/bestsellers",
            f"{self.base_url}/deals",
        ]
        for url in urls:
            try:
                resp = await self._fetch(url)
                soup = BeautifulSoup(resp.text, "lxml")
                for item in soup.select("[data-asin]"):
                    asin = item.get("data-asin")
                    if not asin or asin == "":
                        continue
                    name_el = item.select_one("h2, .a-text-normal")
                    price_el = item.select_one(".a-price-whole, .a-offscreen")
                    if name_el and price_el:
                        price_text = re.sub(r"[^\d.,]", "", price_el.get_text(strip=True))
                        products.append({
                            "name": name_el.get_text(strip=True)[:500],
                            "price": float(price_text.replace(",", ".")) if price_text else 0,
                            "url": f"{self.base_url}/dp/{asin}",
                            "sku": asin,
                            "currency": "EUR",
                        })
            except Exception as e:
                self.log.warning(f"Amazon scrape failed for {url}: {e}")
        return products
