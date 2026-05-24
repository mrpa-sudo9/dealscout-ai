from typing import Any

from scrapers.base import BaseScraper


class MediaMarktScraper(BaseScraper):
    marketplace = "mediamarkt"
    base_url = "https://www.mediamarkt.de"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        url = f"{self.base_url}/deals"
        try:
            resp = await self._fetch(url)
            import json
            import re
            data = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', resp.text)
            if data:
                state = json.loads(data.group(1))
                for item in state.get("products", state.get("items", [])):
                    products.append({
                        "name": item.get("name", "")[:500],
                        "price": float(item.get("price", {}).get("current", item.get("price", 0))),
                        "url": f"{self.base_url}{item.get('url', '')}",
                        "sku": str(item.get("sku", item.get("id", ""))),
                        "currency": "EUR",
                    })
        except Exception as e:
            self.log.warning(f"MediaMarkt scrape failed: {e}")
        return products
