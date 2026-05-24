from typing import Any

from scrapers.base import BaseScraper


class FnacScraper(BaseScraper):
    marketplace = "fnac"
    base_url = "https://www.fnac.com"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        url = f"{self.base_url}/promotions"
        try:
            resp = await self._fetch(url)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            for item in soup.select(".article-card, .product-card"):
                name_el = item.select_one(".title, .product-name")
                price_el = item.select_one(".price, .current-price")
                link_el = item.select_one("a[href]")
                if name_el and price_el:
                    href = link_el.get("href", "") if link_el else ""
                    products.append({
                        "name": name_el.get_text(strip=True)[:500],
                        "price": self._parse_price(price_el.get_text(strip=True)),
                        "url": f"{self.base_url}{href}" if href.startswith("/") else href,
                        "sku": href.split("/")[-2] if href else "",
                        "currency": "EUR",
                    })
        except Exception as e:
            self.log.warning(f"Fnac scrape failed: {e}")
        return products

    def _parse_price(self, text: str) -> float:
        import re
        text = text.replace("\u20ac", "").replace(",", ".").strip()
        nums = re.findall(r"\d+\.?\d*", text)
        return float(nums[0]) if nums else 0
