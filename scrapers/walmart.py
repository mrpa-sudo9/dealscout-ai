from typing import Any

from scrapers.base import BaseScraper


class WalmartScraper(BaseScraper):
    marketplace = "walmart"
    base_url = "https://www.walmart.com"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        url = f"{self.base_url}/cp/deals"
        try:
            resp = await self._fetch(url)
            import json
            import re
            data = re.search(r'window\.__WML_REDUX_INITIAL_STATE__\s*=\s*({.*?});', resp.text)
            if data:
                state = json.loads(data.group(1))
                for item in state.get("products", []):
                    products.append({
                        "name": item.get("name", "")[:500],
                        "price": float(item.get("price", 0)),
                        "url": f"{self.base_url}/ip/{item.get('usItemId', '')}",
                        "sku": str(item.get("usItemId", "")),
                        "currency": "USD",
                        "image_url": item.get("image", ""),
                    })
        except Exception as e:
            self.log.warning(f"Walmart scrape failed: {e}")
        return products
