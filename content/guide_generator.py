import asyncio
import re
from typing import Any

from core.config import settings
from database.models import ChannelType
from utils.logger import log


NICHE_GUIDE_CONFIG = {
    "fashion": {
        "title": "Guida all'Acquisto Moda",
        "h1": "Guida all'Acquisto Moda & Accessori",
        "desc": "Tutto quello che devi sapere per acquistare abbigliamento, scarpe, borse e accessori moda online con i migliori prezzi.",
    },
    "toys": {
        "title": "Guida all'Acquisto Giochi",
        "h1": "Guida all'Acquisto Giochi & Giocattoli",
        "desc": "I migliori giochi e giocattoli per bambini di ogni età. Consigli e confronti per acquisti intelligenti.",
    },
    "sports": {
        "title": "Guida all'Acquisto Sport",
        "h1": "Guida all'Acquisto Sport & Fitness",
        "desc": "Attrezzatura fitness, abbigliamento sportivo e accessori per lo sport. Guida completa per allenarti al meglio.",
    },
    "beauty": {
        "title": "Guida all'Acquisto Bellezza",
        "h1": "Guida all'Acquisto Bellezza & Cosmetica",
        "desc": "Scopri i migliori prodotti di bellezza, skincare e cosmetica. Consigli per la cura della persona.",
    },
    "home_kitchen": {
        "title": "Guida all'Acquisto Casa",
        "h1": "Guida all'Acquisto Casa & Cucina",
        "desc": "Pentole, elettrodomestici, organizzazione e arredamento. Tutto per la tua casa ai migliori prezzi.",
    },
    "tech_accessories": {
        "title": "Guida all'Acquisto Tech",
        "h1": "Guida all'Acquisto Tech & Accessori",
        "desc": "Cavi, caricatori, cuffie, custodie e tutti gli accessori tecnologici che ti semplificano la vita.",
    },
    "pet_supplies": {
        "title": "Guida all'Acquisto Animali",
        "h1": "Guida all'Acquisto Animali Domestici",
        "desc": "Cibo, accessori e giochi per cani, gatti e altri animali domestici. Prenditi cura del tuo amico a 4 zampe.",
    },
    "health_wellness": {
        "title": "Guida all'Acquisto Salute",
        "h1": "Guida all'Acquisto Salute & Benessere",
        "desc": "Integratori, prodotti ortopedici e benessere fisico. Prenditi cura di te stesso con i migliori prodotti.",
    },
}

SYSTEM_PROMPT = """Sei un copywriter SEO italiano specializzato in guide all'acquisto e content marketing.
Scrivi contenuti originali, utili e ben strutturati in ITALIANO.
Usa un tono informativo ma accessibile, come un espero che consiglia un amico.
Non inventare caratteristiche non presenti nei dati forniti.
Includi sempre link di affiliazione in modo naturale nel contesto."""


def _build_guide_prompt(niche: str, products: list[dict[str, Any]]) -> str:
    config = NICHE_GUIDE_CONFIG.get(niche, {})
    products_text = "\n".join(
        f"- {p['name']}: {p['price']}€. Link: {p['link']}. {'Categoria: ' + p.get('category', '') if p.get('category') else ''}"
        for p in products[:20]
    )
    return f"""Genera una GUIDA ALL'ACQUISTO completa in ITALIANO per la nicchia: {config.get('h1', niche)}.

LINEE GUIDA:
- Titolo SEO: {config.get('title', '')}
- H1: {config.get('h1', '')}
- Meta description: {config.get('desc', '')}

Struttura richiesta:
1. **INTRODUZIONE** (2-3 paragrafi): Perché questa categoria è importante, cosa considerare prima dell'acquisto
2. **FATTORI DA CONSIDERARE** (3-4 punti elenco con spiegazione): Cosa valutare nella scelta
3. **MIGLIORI PRODOTTI** (sezione per ogni prodotto tra quelli elencati, con prezzo, link e perché consigliato)
4. **CONCLUSIONE** (1-2 paragrafi): Consiglio finale

Prodotti disponibili nella nicchia:
{products_text}

Formatta come HTML puro con tag h2, h3, p, ul/li. I link devono essere nel formato <a href="URL">TESTO</a>."""


class GuideGenerator:

    async def generate_guide(self, niche: str, products: list[dict[str, Any]]) -> dict[str, str]:
        config = NICHE_GUIDE_CONFIG.get(niche)
        if not config or not products:
            return {}

        prompt = _build_guide_prompt(niche, products)
        html_content = await self._call_llm(prompt)

        if not html_content:
            html_content = self._fallback_guide(niche, products)

        return {
            "niche": niche,
            "html": html_content,
            "seo_title": config["title"],
            "seo_desc": config["desc"],
            "product_count": len(products),
        }

    async def generate_comparison(self, products: list[dict[str, Any]], niche: str) -> dict[str, str]:
        if len(products) < 2:
            return {}
        p1, p2 = products[0], products[1]
        prompt = f"""Genera un CONFRONTO in ITALIANO tra due prodotti della nicchia {niche}.

Prodotto A: {p1['name']} - {p1['price']}€ - {p1['link']}
Prodotto B: {p2['name']} - {p2['price']}€ - {p2['link']}

Struttura:
1. H2: Introduzione al confronto
2. Tabella HTML comparativa (prezzo, caratteristiche, pro/contro)
3. H2: Analisi dettagliata
4. H2: Quale scegliere? Consiglio finale

Formatta come HTML puro."""
        html = await self._call_llm(prompt)
        if not html:
            return {}
        return {
            "type": "comparison",
            "niche": niche,
            "html": html,
            "products": [p1["name"], p2["name"]],
        }

    async def generate_telegram_post(self, guide: dict[str, str]) -> str | None:
        niche = guide["niche"]
        config = NICHE_GUIDE_CONFIG.get(niche, {})
        prompt = f"""Scrivi un messaggio TELEGRAM in ITALIANO di massimo 400 caratteri per annunciare questa nuova guida all'acquisto:
Titolo: {config.get('title', '')}
Descrizione: {config.get('desc', '')}
Numero prodotti: {guide.get('product_count', 0)}

Tono: entusiasta ma sobrio. Includi 2-3 emoji e invita a leggere la guida."""
        msg = await self._call_llm(prompt)
        return msg

    async def _call_llm(self, prompt: str) -> str | None:
        if not settings.openrouter_api_key and not settings.openai_api_key:
            return None
        api_key = settings.openrouter_api_key or settings.openai_api_key
        base_url = "https://openrouter.ai/api/v1" if settings.openrouter_api_key else "https://api.openai.com/v1"
        model = "openrouter/free" if settings.openrouter_api_key else settings.openai_model or "gpt-4o-mini"
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=20.0, max_retries=0)
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
                    temperature=0.7, max_tokens=2048,
                ),
                timeout=25,
            )
            if resp and resp.choices and resp.choices[0].message.content:
                return resp.choices[0].message.content
        except asyncio.TimeoutError:
            log.warning("Guide LLM timed out")
        except Exception as e:
            log.warning(f"Guide LLM failed: {e}")
        return None

    def _fallback_guide(self, niche: str, products: list[dict[str, Any]]) -> str:
        config = NICHE_GUIDE_CONFIG.get(niche, {})
        items = "\n".join(
            f'<li><a href="{p["link"]}">{p["name"]}</a> — {p["price"]}€</li>'
            for p in products[:20]
        )
        return f"""<h2>Introduzione</h2>
<p>{config.get('desc', '')}</p>

<h2>Fattori da Considerare</h2>
<ul>
<li><strong>Qualità:</strong> Valuta sempre la qualità del prodotto in base alle recensioni degli acquirenti.</li>
<li><strong>Prezzo:</strong> Confronta i prezzi su diverse piattaforme per trovare l'offerta migliore.</li>
<li><strong>Garanzia:</strong> Verifica la garanzia offerta dal produttore o dal venditore.</li>
<li><strong>Spedizione:</strong> Considera i tempi e i costi di spedizione.</li>
</ul>

<h2>Migliori Prodotti</h2>
<ul>{items}</ul>

<h2>Conclusione</h2>
<p>Scegli il prodotto che meglio si adatta alle tue esigenze e al tuo budget. Ricorda di verificare sempre le offerte prima di acquistare.</p>"""
