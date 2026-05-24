from typing import Any

from scrapers.base import BaseScraper


class DecathlonScraper(BaseScraper):
    marketplace = "decathlon"
    base_url = "https://www.decathlon.it"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        url = f"{self.base_url}/promozioni"
        try:
            resp = await self._fetch(url)
            import json
            import re
            data = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', resp.text)
            if data:
                state = json.loads(data.group(1))
                for item in state.get("products", []):
                    products.append({
                        "name": item.get("label", "")[:500],
                        "price": float(item.get("price", {}).get("current", 0)),
                        "url": f"{self.base_url}{item.get('url', '')}",
                        "sku": str(item.get("id", "")),
                        "currency": "EUR",
                        "image_url": item.get("image", ""),
                    })
        except Exception as e:
            self.log.warning(f"Decathlon scrape failed: {e}")
        return products
