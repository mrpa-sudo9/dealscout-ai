import json
from datetime import datetime

BASE_URL = "https://mrpa-sudo9.github.io/prezzimigliori"
SITE_NAME = "PrezziMigliori"
SITE_DESC = "I migliori prodotti ai prezzi più bassi. Offerte verificate su Amazon, eBay e altri store."
TWITTER_HANDLE = "@PrezziMigliori"


def json_ld_base(is_index: bool = False) -> str:
    org = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": SITE_NAME,
        "url": BASE_URL,
        "description": SITE_DESC,
    }
    if is_index:
        org["potentialAction"] = {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint", "urlTemplate": f"{BASE_URL}/cerca.html?q={{search_term_string}}"},
            "query-input": "required name=search_term_string",
        }
    return f'<script type="application/ld+json">\n{json.dumps(org, indent=2, ensure_ascii=False)}\n</script>'


def json_ld_breadcrumb(items: list[dict]) -> str:
    item_list = [
        {"@type": "ListItem", "position": i + 1, "name": it["name"], "item": it.get("url", BASE_URL)}
        for i, it in enumerate(items)
    ]
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": item_list,
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, indent=2, ensure_ascii=False)}\n</script>'


def json_ld_product(name: str, price: float, url: str, image: str, marketplace: str, category: str, description: str = "") -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "url": url,
        "image": image,
        "category": category,
        "description": description[:200] if description else name,
        "offers": {
            "@type": "Offer",
            "price": f"{price:.2f}",
            "priceCurrency": "EUR",
            "availability": "https://schema.org/InStock",
            "seller": {"@type": "Organization", "name": marketplace},
        },
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, indent=2, ensure_ascii=False)}\n</script>'


def json_ld_article(headline: str, description: str, date_published: str = "", image: str = "") -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": headline,
        "description": description,
        "publisher": {"@type": "Organization", "name": SITE_NAME},
        "mainEntityOfPage": {"@type": "WebPage", "@id": BASE_URL},
    }
    if date_published:
        data["datePublished"] = date_published
    if image:
        data["image"] = image
    return f'<script type="application/ld+json">\n{json.dumps(data, indent=2, ensure_ascii=False)}\n</script>'


def json_ld_webpage(name: str, description: str, url: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": name,
        "description": description,
        "url": url,
        "publisher": {"@type": "Organization", "name": SITE_NAME},
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, indent=2, ensure_ascii=False)}\n</script>'


def meta_og(title: str, desc: str, url: str, type_: str = "website", image: str = "") -> str:
    tags = f"""    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:type" content="{type_}">
    <meta property="og:url" content="{url}">
    <meta property="og:site_name" content="{SITE_NAME}">
    <meta property="og:locale" content="it_IT">"""
    if image:
        tags += f'\n    <meta property="og:image" content="{image}">'
    return tags


def meta_twitter(title: str, desc: str, image: str = "") -> str:
    tags = f"""    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:site" content="{TWITTER_HANDLE}">"""
    if image:
        tags += f'\n    <meta name="twitter:image" content="{image}">'
    return tags


def seo_meta_block(title: str, desc: str, url: str, type_: str = "website", image: str = "", keywords: str = "") -> str:
    kw_tag = f'\n    <meta name="keywords" content="{keywords}">' if keywords else ""
    return f"""    <title>{title} - {SITE_NAME}</title>
    <meta name="description" content="{desc}">
    <link rel="canonical" href="{url}">
    <meta name="robots" content="index, follow">
    <meta name="google-site-verification" content="UtkaraKoCMQLuBP3LjGepvSNxlwrHQ0PZQ3hz6DoNL0">
{resource_hints()}""" + kw_tag + f"""
{meta_og(title, desc, url, type_, image)}
{meta_twitter(title, desc, image)}"""


def breadcrumb_html(items: list[dict]) -> str:
    crumbs = "".join(
        f'<a href="{it["url"]}">{it["name"]}</a>'
        if i < len(items) - 1
        else f'<span>{it["name"]}</span>'
        for i, it in enumerate(items)
    )
    return f'<nav class="breadcrumb" aria-label="Breadcrumb">{crumbs}</nav>'


def analytics_gtag(measurement_id: str = "G-XXXXXXXX") -> str:
    return f"""    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{measurement_id}');
    </script>"""


def resource_hints() -> str:
    return """    <link rel="dns-prefetch" href="//images-na.ssl-images-amazon.com">
    <link rel="dns-prefetch" href="//m.media-amazon.com">
    <link rel="dns-prefetch" href="//i.ebayimg.com">
    <link rel="dns-prefetch" href="//upload.wikimedia.org">
    <link rel="preconnect" href="https://images-na.ssl-images-amazon.com" crossorigin>
    <link rel="preconnect" href="https://m.media-amazon.com" crossorigin>
    <link rel="preconnect" href="https://i.ebayimg.com" crossorigin>
"""

ROBOTS_TXT = f"""User-agent: *
Allow: /
Sitemap: {BASE_URL}/sitemap.xml
"""


ELECTRONICS_PRICE_TIERS = {
    "base": {"name": "Base", "label": "Entry Level", "min": 0, "max": 100, "desc": "elettronica economica"},
    "media": {"name": "Media", "label": "Mid Range", "min": 100, "max": 300, "desc": "elettronica fascia media"},
    "alta": {"name": "Alta", "label": "Alta Gamma", "min": 300, "max": 600, "desc": "elettronica alta gamma"},
    "top_gamma": {"name": "Top Gamma", "label": "Premium", "min": 600, "max": 1000, "desc": "elettronica premium"},
    "elite": {"name": "Elite", "label": "Elite", "min": 1000, "max": 100000, "desc": "elettronica di lusso"},
}

NICHE_KEYWORDS = {
    "fashion": "moda, scarpe, borse, orologi, abbigliamento, accessori, offerte moda, sconti abbigliamento",
    "toys": "giochi, giocattoli, LEGO, puzzle, giochi da tavolo, offerte giocattoli, sconti giochi",
    "sports": "sport, fitness, yoga, running, biciclette, palestra, attrezzatura sportiva, offerte sport",
    "beauty": "bellezza, cosmetici, makeup, skincare, profumi, cura pelle, offerte bellezza, sconti cosmetici",
    "home_kitchen": "casa, cucina, pentole, elettrodomestici, arredamento, organizzazione casa, offerte casa",
    "tech_accessories": "tecnologia, accessori, cavi, caricatori, cuffie, custodie, gadget, offerte tech",
    "pet_supplies": "animali domestici, cane, gatto, cibo animali, cucce, accessori animali, offerte pet",
    "health_wellness": "salute, benessere, integratori, ortopedia, prodotti benessere, offerte salute",
    "electronics": "elettronica, smartphone, laptop, tablet, cuffie, smartwatch, tecnologia, offerte elettronica",
}



