from typing import Any

from scrapers.base import BaseScraper


class ManoManoScraper(BaseScraper):
    marketplace = "manomano"
    base_url = "https://www.manomano.it"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        url = f"{self.base_url}/promozioni"
        try:
            resp = await self._fetch(url)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            for item in soup.select("[data-offer-id]"):
                offer_id = item.get("data-offer-id", "")
                name_el = item.select_one(".title, .product-title, h2, h3")
                price_el = item.select_one(".price, .current-price")
                if offer_id and name_el:
                    products.append({
                        "name": name_el.get_text(strip=True)[:500],
                        "price": self._parse_price(price_el.get_text(strip=True)) if price_el else 0,
                        "url": f"{self.base_url}/p/{offer_id}",
                        "sku": offer_id,
                        "currency": "EUR",
                    })
        except Exception as e:
            self.log.warning(f"ManoMano scrape failed: {e}")
        return products

    def _parse_price(self, text: str) -> float:
        import re
        nums = re.findall(r"\d+[\.,]?\d*", text.replace(".", "").replace(",", "."))
        return float(nums[0]) if nums else 0
