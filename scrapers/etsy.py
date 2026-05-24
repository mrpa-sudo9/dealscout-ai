from typing import Any

from scrapers.base import BaseScraper


class EtsyScraper(BaseScraper):
    marketplace = "etsy"
    base_url = "https://www.etsy.com"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        url = f"{self.base_url}/featured/deals"
        try:
            resp = await self._fetch(url)
            import json
            import re
            data = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', resp.text)
            if data:
                state = json.loads(data.group(1))
                for item in state.get("results", []):
                    price = (item.get("price", {}) or {}).get("amount", 0)
                    if price:
                        products.append({
                            "name": item.get("title", "")[:500],
                            "price": float(price) / 100,
                            "url": item.get("url", ""),
                            "sku": str(item.get("listing_id", "")),
                            "currency": "EUR",
                        })
        except Exception as e:
            self.log.warning(f"Etsy scrape failed: {e}")
        return products
