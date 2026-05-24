import re
from typing import Any

from scrapers.base import BaseScraper


class EbayScraper(BaseScraper):
    marketplace = "ebay"
    base_url = "https://www.ebay.com"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        try:
            soup = await self._fetch_soup(f"{self.base_url}/deals/")
            for item in soup.select(".dne-itemtile"):
                listing_id = item.get("data-listing-id", "")
                title_el = item.select_one(".dne-itemtile-title")
                price_el = item.select_one(".dne-itemtile-price")
                link_el = item.select_one("a[href*='/itm/']")

                if not title_el or not price_el:
                    continue

                price_text = price_el.get_text(strip=True)
                price = self._parse_price(price_text)
                if price == 0:
                    meta = price_el.select_one("meta[itemprop='price']")
                    if meta:
                        price = float(meta.get("content", 0))

                href = link_el.get("href", "") if link_el else f"https://www.ebay.com/itm/{listing_id}"

                products.append({
                    "name": title_el.get_text(strip=True)[:500],
                    "price": price,
                    "url": href,
                    "sku": listing_id,
                    "currency": "USD",
                    "marketplace": "ebay",
                })
        except Exception as e:
            self.log.warning(f"eBay scrape failed: {e}")

        self.log.info(f"[eBay] Scraped {len(products)} products")
        return products

    def _parse_price(self, text: str) -> float:
        text = text.replace("EUR", "").replace("euro", "").replace("$", "").replace(" ", "").split(" a ")[0]
        nums = re.findall(r"\d+\.?\d*", text.replace(",", "."))
        return float(nums[0]) if nums else 0
