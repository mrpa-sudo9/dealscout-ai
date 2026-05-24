from typing import Any

from scrapers.base import BaseScraper


class ZalandoScraper(BaseScraper):
    marketplace = "zalando"
    base_url = "https://www.zalando.it"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        url = f"{self.base_url}/outlet"
        try:
            resp = await self._fetch(url)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            for article in soup.select("[data-articleid]"):
                article_id = article.get("data-articleid", "")
                name_el = article.select_one(".cat_brand, h3")
                price_el = article.select_one(".sale_price, .price")
                if article_id and name_el:
                    products.append({
                        "name": name_el.get_text(strip=True)[:500],
                        "price": self._parse_price(price_el.get_text(strip=True)) if price_el else 0,
                        "url": f"{self.base_url}/article/{article_id}",
                        "sku": article_id,
                        "currency": "EUR",
                    })
        except Exception as e:
            self.log.warning(f"Zalando scrape failed: {e}")
        return products

    def _parse_price(self, text: str) -> float:
        import re
        nums = re.findall(r"\d+[\.,]?\d*", text.replace(".", "").replace(",", "."))
        return float(nums[0]) if nums else 0
