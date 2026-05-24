from typing import Any

from scrapers.base import BaseScraper


class RakutenScraper(BaseScraper):
    marketplace = "rakuten"
    base_url = "https://www.rakuten.co.jp"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        url = f"{self.base_url}/category/deals"
        try:
            resp = await self._fetch(url)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            for item in soup.select(".item, .product"):
                name_el = item.select_one(".title, .item-name, h2, h3")
                price_el = item.select_one(".price, .item-price")
                link_el = item.select_one("a[href]")
                if name_el and price_el:
                    href = link_el.get("href", "") if link_el else ""
                    products.append({
                        "name": name_el.get_text(strip=True)[:500],
                        "price": self._parse_price(price_el.get_text(strip=True)),
                        "url": href if href.startswith("http") else f"{self.base_url}{href}",
                        "sku": href.split("/")[-1] if href else "",
                        "currency": "JPY",
                    })
        except Exception as e:
            self.log.warning(f"Rakuten scrape failed: {e}")
        return products

    def _parse_price(self, text: str) -> float:
        import re
        nums = re.findall(r"\d+[\.,]?\d*", text.replace(",", ""))
        return float(nums[0]) if nums else 0
