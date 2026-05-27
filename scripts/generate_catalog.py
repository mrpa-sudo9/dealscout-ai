import asyncio
from pathlib import Path

from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from database.models import Product, Deal, PriceRecord
from database.session import init_db, get_session


NICHE_META = {
    "fashion": {
        "name": "Moda & Accessori",
        "icon": "👕",
        "description": "Scarpe, borse, orologi, abbigliamento e accessori moda",
        "commission": "6%",
    },
    "toys": {
        "name": "Giochi & Giocattoli",
        "icon": "🧸",
        "description": "LEGO, puzzle, giochi da tavolo e giocattoli per bambini",
        "commission": "3%",
    },
    "sports": {
        "name": "Sport & Fitness",
        "icon": "🏋️",
        "description": "Attrezzatura fitness, yoga, running, biciclette e sport",
        "commission": "4%",
    },
    "beauty": {
        "name": "Bellezza & Cosmetica",
        "icon": "💄",
        "description": "Makeup, skincare, profumi e prodotti per la cura personale",
        "commission": "4%",
    },
    "home_kitchen": {
        "name": "Casa & Cucina",
        "icon": "🏠",
        "description": "Pentole, elettrodomestici, organizzazione e arredamento",
        "commission": "5%",
    },
    "tech_accessories": {
        "name": "Tech & Accessori",
        "icon": "📱",
        "description": "Cavi, caricatori, cuffie, custodie e gadget tecnologici",
        "commission": "3%",
    },
    "pet_supplies": {
        "name": "Animali Domestici",
        "icon": "🐾",
        "description": "Cibo, cucce, giochi e accessori per cani, gatti e altri animali",
        "commission": "5%",
    },
    "health_wellness": {
        "name": "Salute & Benessere",
        "icon": "💊",
        "description": "Integratori, prodotti ortopedici e benessere fisico",
        "commission": "4%",
    },
}

MARKETPLACE_LOGOS = {
    "AMAZON": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Amazon_icon.svg/64px-Amazon_icon.svg.png",
    "EBAY": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/EBay_logo.svg/64px-EBay_logo.svg.png",
    "ALIEXPRESS": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/AliExpress_logo.svg/64px-AliExpress_logo.svg.png",
    "OTHER": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Generic_icon.svg/64px-Generic_icon.svg.png",
}


def render_product_card(p, price_float: float = 0.0, is_deal: bool = False, discount: float = 0.0) -> str:
    mp = p.marketplace.value if p.marketplace else "OTHER"
    logo = MARKETPLACE_LOGOS.get(mp, MARKETPLACE_LOGOS["OTHER"])
    price_str = f"{price_float:.2f}" if price_float else "N/D"
    affiliate_url = p.marketplace_url or ""
    if mp == "AMAZON":
        affiliate_url = affiliate_url + ("?tag=mrpa96-21" if "?" not in affiliate_url else "&tag=mrpa96-21")
    elif mp == "EBAY":
        affiliate_url = affiliate_url  # no EPN tag yet

    deal_badge = f'<span class="deal-badge">-{discount:.0f}%</span>' if is_deal and discount else ""

    return f"""
    <div class="product-card">
        {deal_badge}
        <div class="product-image">
            <img src="{p.image_url or 'https://via.placeholder.com/200x200?text=' + p.name[:20]}" alt="{p.name}" loading="lazy" onerror="this.src='https://via.placeholder.com/200x200?text=Prodotto'">
        </div>
        <div class="product-info">
            <div class="product-marketplace">
                <img src="{logo}" height="16" alt="{mp}">
                <span>{mp}</span>
            </div>
            <h3 class="product-title">{p.name[:80]}{'...' if len(p.name) > 80 else ''}</h3>
            <div class="product-price">{price_str}€</div>
            {f'<div class="product-description">{" ".join(p.description) if isinstance(p.description, list) else str(p.description)[:120]}...</div>' if p.description else ''}
            <a href="{affiliate_url}" class="product-link" target="_blank" rel="nofollow sponsored">Vedi offerta →</a>
        </div>
    </div>"""


def render_category_page(niche: str, products_with_prices: list) -> str:
    meta = NICHE_META.get(niche, {"name": niche, "icon": "", "description": "", "commission": ""})
    product_cards = "\n".join(render_product_card(p, price) for p, price in products_with_prices)
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{meta['name']} - PrezziMigliori</title>
    <meta name="description" content="{meta['description']}. Scopri i migliori prodotti {meta['name'].lower()} ai prezzi più bassi su Amazon, eBay e altri store.">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="index.html" class="nav-logo">🏷️ PrezziMigliori</a>
            <div class="nav-links">
                <a href="index.html">Home</a>
                <a href="deals.html">Offerte</a>
            </div>
        </div>
    </nav>

    <main class="container">
        <div class="category-header">
            <h1>{meta['icon']} {meta['name']}</h1>
            <p>{meta['description']}</p>
            <p class="commission-note">Commissione Amazon: {meta['commission']}</p>
        </div>

        <div class="products-grid">
            {product_cards}
        </div>
    </main>

    <footer class="footer">
        <div class="container">
            <p>PrezziMigliori - Confronto prezzi indipendente. I link sono affiliati Amazon, eBay e AliExpress.</p>
            <p>&copy; 2026 PrezziMigliori</p>
        </div>
    </footer>
</body>
</html>"""


def render_index_page(category_counts: dict, total_products: int, total_deals: int) -> str:
    category_cards = ""
    for niche, meta in sorted(NICHE_META.items()):
        count = category_counts.get(niche, 0)
        category_cards += f"""
        <a href="{niche}.html" class="category-card">
            <div class="category-icon">{meta['icon']}</div>
            <h3>{meta['name']}</h3>
            <p>{meta['description']}</p>
            <div class="category-stats">
                <span>{count} prodotti</span>
                <span>Comm. {meta['commission']}</span>
            </div>
        </a>"""

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PrezziMigliori - Offerte e Prodotti ai Migliori Prezzi</title>
    <meta name="description" content="Scopri i migliori prodotti nei settori moda, sport, bellezza, casa, tecnologia e animali ai prezzi più bassi. Offerte verificate ogni giorno.">
    <meta name="keywords" content="offerte, prezzi migliori, amazon, ebay, sconti, moda, sport, bellezza, casa, tecnologia">
    <link rel="canonical" href="https://mrpa-sudo9.github.io/prezzimigliori/">
    <link rel="stylesheet" href="style.css">
    <meta property="og:title" content="PrezziMigliori - Offerte e Prodotti ai Migliori Prezzi">
    <meta property="og:description" content="Scopri i migliori prodotti ai prezzi più bassi. Offerte verificate ogni giorno.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://mrpa-sudo9.github.io/prezzimigliori/">
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="index.html" class="nav-logo">🏷️ PrezziMigliori</a>
            <div class="nav-links">
                <a href="index.html">Home</a>
                <a href="deals.html">Offerte ({total_deals})</a>
            </div>
        </div>
    </nav>

    <header class="hero">
        <div class="container">
            <h1>🏷️ PrezziMigliori</h1>
            <p>I migliori prodotti ai prezzi più bassi. {total_products} prodotti in 8 categorie, selezionati per te.</p>
            <div class="hero-stats">
                <div class="stat"><span class="stat-num">{total_products}+</span><span class="stat-label">Prodotti</span></div>
                <div class="stat"><span class="stat-num">{len(NICHE_META)}</span><span class="stat-label">Categorie</span></div>
                <div class="stat"><span class="stat-num">{total_deals}+</span><span class="stat-label">Offerte</span></div>
                <div class="stat"><span class="stat-num">24h</span><span class="stat-label">Aggiornamento</span></div>
            </div>
        </div>
    </header>

    <main class="container">
        <section class="categories-grid">
            {category_cards}
        </section>
    </main>

    <footer class="footer">
        <div class="container">
            <p>PrezziMigliori - Confronto prezzi indipendente. I link sono affiliati Amazon, eBay e AliExpress.</p>
            <p>Partecipa al programma Amazon Associates, eBay Partner Network e AliExpress.</p>
            <p>&copy; 2026 PrezziMigliori</p>
        </div>
    </footer>
</body>
</html>"""


def render_deals_page(deals_with_prices: list) -> str:
    cards = "\n".join(
        render_product_card(d.product, price, is_deal=True, discount=d.discount_percent)
        for d, price in deals_with_prices if hasattr(d, "product") and d.product
    )
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offerte - PrezziMigliori</title>
    <meta name="description" content="Tutte le offerte e sconti attivi. Risparmia sui migliori prodotti.">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="index.html" class="nav-logo">🏷️ PrezziMigliori</a>
            <div class="nav-links">
                <a href="index.html">Home</a>
                <a href="deals.html">Offerte</a>
            </div>
        </div>
    </nav>

    <main class="container">
        <h1>🔥 Offerte Attive</h1>
        <p>Prodotti con sconto verificato. Aggiornato quotidianamente.</p>
        <div class="products-grid">
            {cards}
        </div>
    </main>

    <footer class="footer">
        <div class="container">
            <p>PrezziMigliori - Confronto prezzi indipendente.</p>
            <p>&copy; 2026 PrezziMigliori</p>
        </div>
    </footer>
</body>
</html>"""


STYLE_CSS = """/* PrezziMigliori - Modern Product Catalog */
:root {
    --primary: #e67e22;
    --primary-dark: #d35400;
    --secondary: #2c3e50;
    --bg: #f8f9fa;
    --card-bg: #ffffff;
    --text: #2c3e50;
    --text-light: #7f8c8d;
    --border: #ecf0f1;
    --success: #27ae60;
    --deal-bg: #e74c3c;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
}

.container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }

/* Navbar */
.navbar {
    background: var(--secondary);
    color: white;
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.nav-logo { font-size: 1.5rem; font-weight: 700; text-decoration: none; color: white; }
.nav-links { display: flex; gap: 1.5rem; }
.nav-links a { color: rgba(255,255,255,0.8); text-decoration: none; font-size: 0.95rem; transition: color 0.2s; }
.nav-links a:hover { color: white; }

/* Hero */
.hero {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    padding: 4rem 0;
    text-align: center;
}
.hero h1 { font-size: 2.5rem; margin-bottom: 1rem; }
.hero p { font-size: 1.2rem; opacity: 0.9; max-width: 600px; margin: 0 auto 2rem; }
.hero-stats { display: flex; justify-content: center; gap: 3rem; flex-wrap: wrap; }
.stat { text-align: center; }
.stat-num { display: block; font-size: 2rem; font-weight: 700; }
.stat-label { font-size: 0.9rem; opacity: 0.8; }

/* Categories Grid */
.categories-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
    padding: 3rem 0;
}
.category-card {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 2rem;
    text-decoration: none;
    color: var(--text);
    border: 1px solid var(--border);
    transition: transform 0.2s, box-shadow 0.2s;
}
.category-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}
.category-icon { font-size: 2.5rem; margin-bottom: 1rem; }
.category-card h3 { font-size: 1.3rem; margin-bottom: 0.5rem; }
.category-card p { color: var(--text-light); font-size: 0.9rem; margin-bottom: 1rem; }
.category-stats { display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-light); }

/* Category header */
.category-header {
    padding: 2rem 0;
    text-align: center;
}
.category-header h1 { font-size: 2rem; }
.category-header p { color: var(--text-light); }
.commission-note { font-size: 0.85rem; color: var(--primary); margin-top: 0.5rem; }

/* Products Grid */
.products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1.5rem;
    padding: 2rem 0;
}

/* Product Card */
.product-card {
    background: var(--card-bg);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border);
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
}
.product-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}
.deal-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    background: var(--deal-bg);
    color: white;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
    z-index: 1;
}
.product-image {
    height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f5f6fa;
    padding: 1rem;
}
.product-image img { max-width: 100%; max-height: 180px; object-fit: contain; }
.product-info { padding: 1.2rem; }
.product-marketplace { display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; color: var(--text-light); margin-bottom: 0.5rem; }
.product-title { font-size: 0.95rem; margin-bottom: 0.5rem; line-height: 1.3; min-height: 2.6em; }
.product-description { font-size: 0.8rem; color: var(--text-light); margin-bottom: 0.5rem; }
.product-price { font-size: 1.3rem; font-weight: 700; color: var(--primary); margin-bottom: 0.8rem; }
.product-link {
    display: block;
    text-align: center;
    background: var(--primary);
    color: white;
    padding: 0.6rem;
    border-radius: 8px;
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 600;
    transition: background 0.2s;
}
.product-link:hover { background: var(--primary-dark); }

/* Footer */
.footer {
    background: var(--secondary);
    color: rgba(255,255,255,0.7);
    text-align: center;
    padding: 2rem 0;
    margin-top: 3rem;
    font-size: 0.85rem;
}
.footer p { margin-bottom: 0.5rem; }

/* Responsive */
@media (max-width: 768px) {
    .hero h1 { font-size: 1.8rem; }
    .hero-stats { gap: 1.5rem; }
    .categories-grid { grid-template-columns: 1fr; }
    .products-grid { grid-template-columns: 1fr; }
}
"""


async def main():
    await init_db()

    out_dir = Path("/tmp/prezzimigliori")
    out_dir.mkdir(parents=True, exist_ok=True)

    async for session in get_session():
        all_products = (await session.execute(select(Product))).scalars().all()

        latest_price_subq = (
            select(PriceRecord.product_id, func.max(PriceRecord.recorded_at).label("max_date"))
            .group_by(PriceRecord.product_id)
            .subquery()
        )
        prices = (await session.execute(
            select(PriceRecord.product_id, PriceRecord.price)
            .join(latest_price_subq, (PriceRecord.product_id == latest_price_subq.c.product_id) & (PriceRecord.recorded_at == latest_price_subq.c.max_date))
        )).all()
        price_map = {pid: float(pr) for pid, pr in prices}

        def get_price(p: Product) -> float:
            return price_map.get(p.id, 0.0)

        deals = (await session.execute(
            select(Deal).options(
                joinedload(Deal.product)
            ).order_by(Deal.discount_percent.desc()).limit(60)
        )).scalars().all()

        category_counts = {}
        for niche in NICHE_META:
            cat_products = [(p, get_price(p)) for p in all_products if p.category == niche]
            category_counts[niche] = len(cat_products)
            if cat_products:
                html = render_category_page(niche, cat_products)
                (out_dir / f"{niche}.html").write_text(html, encoding="utf-8")
                print(f"Generated {niche}.html: {len(cat_products)} products")

        index_html = render_index_page(category_counts, len(all_products), len(deals))
        (out_dir / "index.html").write_text(index_html, encoding="utf-8")
        print(f"Generated index.html: {len(all_products)} total products")

        deals_with_prices = [(d, get_price(d.product)) for d in deals if hasattr(d, "product") and d.product]
        deals_html = render_deals_page(deals_with_prices)
        (out_dir / "deals.html").write_text(deals_html, encoding="utf-8")
        print(f"Generated deals.html: {len(deals_with_prices)} deals")

        (out_dir / "style.css").write_text(STYLE_CSS, encoding="utf-8")
        print("Generated style.css")

    print("\n✅ Catalogo generato!")


if __name__ == "__main__":
    asyncio.run(main())
