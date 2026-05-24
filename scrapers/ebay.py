from typing import Any

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper


class EbayScraper(BaseScraper):
    marketplace = "ebay"
    base_url = "https://www.ebay.it"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        urls = [
            f"{self.base_url}/sch/Deals",
            f"{self.base_url}/globaldeals",
        ]
        for url in urls:
            try:
                resp = await self._fetch(url)
                soup = BeautifulSoup(resp.text, "lxml")
                for item in soup.select(".s-item"):
                    link_el = item.select_one(".s-item__link")
                    price_el = item.select_one(".s-item__price")
                    title_el = item.select_one(".s-item__title")
                    if link_el and price_el and title_el:
                        href = link_el.get("href", "")
                        item_id = href.split("?")[0].split("/")[-1] if "/itm/" in href else ""
                        products.append({
                            "name": title_el.get_text(strip=True)[:500],
                            "price": self._parse_price(price_el.get_text(strip=True)),
                            "url": href,
                            "sku": item_id,
                            "currency": "EUR",
                        })
            except Exception as e:
                self.log.warning(f"eBay scrape failed: {e}")
        return products

    def _parse_price(self, text: str) -> float:
        text = text.replace("EUR", "").replace("euro", "").replace(" ", "").split(" a ")[0]
        text = text.replace(",", ".")
        import re
        nums = re.findall(r"\d+\.?\d*", text)
        return float(nums[0]) if nums else 0
