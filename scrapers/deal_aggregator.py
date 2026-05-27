import re
from datetime import datetime, timezone
from typing import Any

import feedparser

from scrapers.base import BaseScraper


class DealAggregatorScraper(BaseScraper):
    """Scrapes deal aggregator RSS feeds (Pepper.it, mydealz, etc.).

    These aggregators collect deals from all major marketplaces,
    making them a single reliable source instead of 12 fragile scrapers.
    """

    marketplace = "deal_aggregator"
    base_url = ""

    FEEDS = [
        "https://www.pepper.it/deals/feed/rss",
        "https://www.pepper.it/deals/feed/rss?category=3",
        "https://www.pepper.it/tag/amazon/feed/rss",
        "https://www.pepper.it/tag/offerte-sport/feed/rss",
        "https://www.pepper.it/tag/cucina/feed/rss",
        "https://www.pepper.it/tag/bellezza/feed/rss",
        "https://www.pepper.it/tag/tecnologia/feed/rss",
        "https://www.pepper.it/tag/moda-trendy/feed/rss",
        "https://www.pepper.it/tag/animali-domestici/feed/rss",
        "https://www.pepper.it/tag/salute/feed/rss",
        "https://www.mydealz.de/deals/feed/rss",
        "https://www.mydealz.de/deals/feed/rss?category=3",
    ]

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        seen_urls = set()

        for feed_url in self.FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:30]:
                    url = entry.get("link", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    title = entry.get("title", "")
                    if not title:
                        continue

                    price = self._extract_price(title, entry)
                    marketplace = self._detect_marketplace(title, url)
                    sku = self._extract_sku(url)

                    products.append({
                        "name": re.sub(r"\s+", " ", title).strip()[:500],
                        "price": price,
                        "url": url,
                        "sku": sku or str(hash(url)),
                        "currency": "EUR",
                        "marketplace": marketplace,
                        "source": "rss_aggregator",
                    })
            except Exception as e:
                self.log.warning(f"RSS feed failed {feed_url}: {e}")

        self.log.info(f"[DealAggregator] Scraped {len(products)} deals from RSS")
        return products

    def _extract_price(self, title: str, entry: Any) -> float:
        content = title + " " + (entry.get("summary", "") or "")
        nums = re.findall(r"(?:€|EUR|euro)\s*(\d+[\.,]?\d*)", content, re.I)
        if not nums:
            nums = re.findall(r"(\d+[\.,]?\d*)\s*(?:€|EUR|euro)", content, re.I)
        if not nums:
            nums = re.findall(r"\b(\d+[\.,]\d{2})\b", content)
        if nums:
            return float(nums[0].replace(",", "."))
        return 0.0

    def _detect_marketplace(self, title: str, url: str) -> str:
        combined = (title + " " + url).lower()
        for name, keywords in [
            ("amazon", ["amazon", "amzn"]),
            ("ebay", ["ebay"]),
            ("etsy", ["etsy"]),
            ("aliexpress", ["aliexpress", "alibaba"]),
            ("decathlon", ["decathlon"]),
            ("zalando", ["zalando"]),
            ("mediamarkt", ["mediamarkt", "media markt"]),
            ("fnac", ["fnac"]),
            ("manomano", ["manomano", "mano mano"]),
            ("walmart", ["walmart"]),
            ("rakuten", ["rakuten"]),
        ]:
            if any(k in combined for k in keywords):
                return name
        return "generic"

    def _extract_sku(self, url: str) -> str:
        patterns = [
            r"/dp/([A-Z0-9]{10})",
            r"/itm/(\d+)",
            r"product-(\w+)",
            r"item/(\d+)",
            r"-(\d{7,})\b",
        ]
        for pat in patterns:
            m = re.search(pat, url)
            if m:
                return m.group(1)
        return ""
