from typing import Any

from scrapers.base import BaseScraper


class AliExpressScraper(BaseScraper):
    marketplace = "aliexpress"
    base_url = "https://www.aliexpress.com"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        url = f"{self.base_url}/af/category/1.html"
        try:
            resp = await self._fetch(url)
            import json
            import re
            data = re.search(r'window\.__NUXT__\s*=\s*({.*?});', resp.text)
            if data:
                state = json.loads(data.group(1))
                items = (state.get("data", {}) or {}).get("items", [])
                for item in items:
                    products.append({
                        "name": item.get("title", "")[:500],
                        "price": float(item.get("price", 0)),
                        "url": f"{self.base_url}/item/{item.get('itemId')}.html",
                        "sku": str(item.get("itemId", "")),
                        "currency": "EUR",
                    })
        except Exception as e:
            self.log.warning(f"AliExpress scrape failed: {e}")
        return products
