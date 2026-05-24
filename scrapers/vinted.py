from typing import Any

from scrapers.base import BaseScraper


class VintedScraper(BaseScraper):
    marketplace = "vinted"
    base_url = "https://www.vinted.it"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        url = f"{self.base_url}/catalog?search_text=&order=newest_first&price_from=1&price_to=50"
        try:
            resp = await self._fetch(url)
            import json
            import re
            data = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', resp.text)
            if data:
                state = json.loads(data.group(1))
                for item in state.get("items", []):
                    products.append({
                        "name": item.get("title", "")[:500],
                        "price": float(item.get("price", {}).get("amount", 0)),
                        "url": f"{self.base_url}/items/{item.get('id')}",
                        "sku": str(item.get("id", "")),
                        "currency": "EUR",
                        "image_url": item.get("photo", {}).get("url", ""),
                    })
        except Exception as e:
            self.log.warning(f"Vinted scrape failed: {e}")
        return products
