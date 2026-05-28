import asyncio
import re
from typing import Any

import feedparser

from scrapers.base import BaseScraper


NICHE_SEARCH_TERMS: dict[str, list[str]] = {
    "fashion": [
        "sneakers+uomo", "borsa+donna", "orologio+uomo", "scarpe+running",
        "giacca+uomo", "pantaloni+moda", "cappotto+donna", "zaino+scuola",
    ],
    "sports": [
        "attrezzatura+fitness", "yoga+mat", "pesi+manubri", "bicicletta+elettrica",
        "scarpe+calcio", "pallone+calcio", "casco+bici", "smartwatch+sport",
    ],
    "beauty": [
        "crema+viso", "profumo+uomo", "makeup+kit", "phon+capelli",
        "rasoio+elettrico", "shampoo+professionale", "siero+antirughe",
    ],
    "home_kitchen": [
        "caffettiera", "pentola+acciaio", "coltelli+cucina", "organizer+casa",
        "lampada+design", "cuscino+memory", "lenzuola+matrimoniali", "tappeto+salotto",
    ],
    "tech_accessories": [
        "power+bank", "cavo+usb+c", "caricatore+wireless", "custodia+iphone",
        "airpods+case", "hub+usb+c", "mouse+wireless", "tastiera+meccanica",
    ],
    "pet_supplies": [
        "cuccia+cane", "tiragraffi+gatto", "guinzaglio+cane", "fontanella+gatto",
        "cibo+secco+cane", "lettiera+gatto", "trasportino+animali",
    ],
    "health_wellness": [
        "cuscino+ortopedico", "massaggiatore+muscolare", "integratore+magnesio",
        "bilancia+pesapersone", "tappetino+yoga", "pistola+massaggio",
    ],
    "electronics": [
        "smartphone+android", "iphone+nuovo", "laptop+offerte", "tablet+android",
        "cuffie+wireless", "smartwatch+offerte", "tv+oled+offerta", "monitor+pc",
        "cuffie+noise+cancelling", "action+camera", "console+ps5", "kindle+offerta",
    ],
}


class EbayScraper(BaseScraper):
    marketplace = "ebay"
    base_url = "https://www.ebay.it"

    async def scrape(self) -> list[dict[str, Any]]:
        products = []
        seen_ids = set()

        try:
            soup = await self._fetch_soup(f"{self.base_url}/deals/")
            for item in soup.select(".dne-itemtile"):
                listing_id = item.get("data-listing-id", "")
                title_el = item.select_one(".dne-itemtile-title")
                price_el = item.select_one(".dne-itemtile-price")
                link_el = item.select_one("a[href*='/itm/']")

                if not title_el or not price_el:
                    continue

                listing_id = listing_id or str(hash(link_el.get("href", "")) if link_el else "")
                if not listing_id or listing_id in seen_ids:
                    continue
                seen_ids.add(listing_id)

                price_text = price_el.get_text(strip=True)
                price = self._parse_price(price_text)
                if price == 0:
                    meta = price_el.select_one("meta[itemprop='price']")
                    if meta:
                        price = float(meta.get("content", 0))

                href = link_el.get("href", "") if link_el else f"https://www.ebay.it/itm/{listing_id}"
                if price == 0:
                    continue

                products.append({
                    "name": title_el.get_text(strip=True)[:500],
                    "price": price,
                    "url": href,
                    "sku": listing_id,
                    "currency": "EUR",
                    "marketplace": "ebay",
                })
        except Exception as e:
            self.log.warning(f"eBay deals scrape failed: {e}")

        # eBay search via global deals pages (less bot-prone than /sch/)
        US_DEALS_URLS = [
            "https://www.ebay.com/globaldeals/",
            "https://www.ebay.com/globaldeals/fashion",
            "https://www.ebay.com/globaldeals/tech",
            "https://www.ebay.com/globaldeals/home",
            "https://www.ebay.com/globaldeals/sports",
        ]
        for deals_url in US_DEALS_URLS:
            try:
                await asyncio.sleep(2)
                soup = await self._fetch_soup(deals_url)
                for item in soup.select("[data-testid='deal-item']") or soup.select(".dne-itemtile") or soup.select("[class*='card']"):
                    title_el = item.select_one("[data-testid='title']") or item.select_one(".dne-itemtile-title") or item.select_one("[class*='title']")
                    price_el = item.select_one("[data-testid='price']") or item.select_one(".dne-itemtile-price") or item.select_one("[class*='price']")
                    link_el = item.select_one("a[href*='itm']") or item.select_one("a[href*='sch']")

                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue

                    href = link_el.get("href", "") if link_el else ""
                    listing_id = ""
                    m = re.search(r"/itm/(\d+)", href)
                    if m:
                        listing_id = m.group(1)
                    listing_id = listing_id or str(hash(href))
                    if listing_id in seen_ids:
                        continue
                    seen_ids.add(listing_id)

                    price = 0.0
                    if price_el:
                        price_text = price_el.get_text(strip=True)
                        price = self._parse_price(price_text)
                    if price == 0:
                        continue

                    products.append({
                        "name": title[:500],
                        "price": price,
                        "url": href.split("?")[0] if href else "",
                        "sku": listing_id,
                        "currency": "EUR",
                        "marketplace": "ebay",
                    })
            except Exception as e:
                self.log.warning(f"eBay global deals failed for '{deals_url}': {e}")

        # Fallback: eBay RSS feed (more reliable than scraping)
        EBAY_RSS_FEEDS = [
            "https://www.ebay.com/deals/feed/rss",
            "https://www.ebay.com/rpp/feed/buying-guides",
        ]
        for rss_url in EBAY_RSS_FEEDS:
            try:
                feed = feedparser.parse(rss_url)
                for entry in feed.entries[:40]:
                    url = entry.get("link", "")
                    title = entry.get("title", "")
                    if not title or not url:
                        continue
                    listing_id = ""
                    m = re.search(r"/itm/(\d+)", url)
                    if m:
                        listing_id = m.group(1)
                    listing_id = listing_id or str(hash(url))
                    if listing_id in seen_ids:
                        continue
                    seen_ids.add(listing_id)

                    price = 0.0
                    summary = entry.get("summary", "") or entry.get("description", "") or ""
                    nums = re.findall(r"(?:€|EUR|\$|USD)\s*(\d+[\.,]?\d*)", title + " " + summary, re.I)
                    if nums:
                        price = float(nums[0].replace(",", "."))
                    else:
                        nums = re.findall(r"\b(\d+[\.,]\d{2})\b", title + " " + summary)
                        if nums:
                            price = float(nums[0].replace(",", "."))
                        else:
                            continue

                    if price == 0:
                        continue

                    products.append({
                        "name": re.sub(r"\s+", " ", title).strip()[:500],
                        "price": price,
                        "url": url,
                        "sku": listing_id,
                        "currency": "EUR",
                        "marketplace": "ebay",
                    })
            except Exception as e:
                self.log.warning(f"eBay RSS failed for '{rss_url}': {e}")

        self.log.info(f"[eBay] Scraped {len(products)} products ({len(seen_ids)} unique)")
        return products

    def _parse_price(self, text: str) -> float:
        text = text.replace("EUR", "").replace("€", "").replace("$", "").replace(" ", "").split(" a ")[0]
        nums = re.findall(r"\d+\.?\d*", text.replace(",", "."))
        return float(nums[0]) if nums else 0
