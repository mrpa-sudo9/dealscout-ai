from typing import Any

from core.config import settings
from database.models import ChannelType
from utils.logger import log


class ContentGenerator:
    SYSTEM_PROMPT = """Sei un esperto copywriter specializzato nella promozione di offerte shopping online. 
Devi creare contenuti in italiano per promuovere un prodotto scontato.

Tono di voce: entusiasta ma affidabile, senza esagerazioni. Non usare mai parole come "imperdibile" o "pazzesco", 
sii concreto. Includi sempre una nota di urgenza solo se reale (es. offerta a tempo). 
Non inventare caratteristiche non presenti nei dati forniti."""

    async def generate_all(self, payload: dict[str, Any]) -> dict[ChannelType, str]:
        prompt = self._build_prompt(payload)

        texts = await self._call_llm(prompt)
        if texts:
            return self._parse_response(texts, payload)

        return self._fallback_templates(payload)

    def _build_prompt(self, p: dict) -> str:
        return f"""Genera i seguenti contenuti per il prodotto, ciascuno separato da "---" e con l'indicazione del canale:

Dati prodotto:
- Nome: {p['product_name']}
- Prezzo attuale: {p['current_price']}€
- Prezzo medio: {p['avg_price']}€
- Sconto: {p['discount']}%
- Piattaforma: {p['marketplace']}
- Link: {p['affiliate_link']}

1. **TWITTER**: 4 tweet separati da "|". Primo hook forte con sconto. Terzo tweet col link.
2. **TELEGRAM**: Messaggio breve di 3-4 righe con emoji e link.
3. **FACEBOOK**: Post 150-200 parole, tono amichevole, finisce con "Acquistalo qui 👉 [link]"
4. **INSTAGRAM**: 5 slide per carosello. Slide 1: hook. Slide 2-4: caratteristiche. Slide 5: CTA.
5. **PINTEREST**: Descrizione SEO 2-3 righe con hashtag e link.
6. **WORDPRESS**: Titolo SEO, meta description, articolo 500+ parole con 3 sottotitoli H2.
7. **REDDIT**: Post 100-150 parole che sembra un consiglio genuino, non pubblicità.
8. **NEWSLETTER**: Oggetto (max 50 char) + corpo email con storia d'uso e CTA."""

    async def _call_llm(self, prompt: str) -> str | None:
        if settings.gemini_api_key:
            try:
                from google import genai
                client = genai.Client(api_key=settings.gemini_api_key)
                resp = await client.aio.models.generate_content(
                    model=settings.gemini_model,
                    contents=prompt,
                    config={"system_instruction": self.SYSTEM_PROMPT},
                )
                if resp.text:
                    return resp.text
            except Exception as e:
                log.warning(f"Gemini API failed: {e}")

        if settings.groq_api_key:
            try:
                from groq import AsyncGroq
                client = AsyncGroq(api_key=settings.groq_api_key)
                resp = await client.chat.completions.create(
                    model=settings.groq_model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=4096,
                )
                return resp.choices[0].message.content
            except Exception as e:
                log.warning(f"Groq API failed: {e}, falling back to OpenAI")

        if settings.openai_api_key:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=settings.openai_api_key)
                resp = await client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=4096,
                )
                return resp.choices[0].message.content
            except Exception as e:
                log.warning(f"OpenAI API failed: {e}")

        return None

    def _parse_response(self, text: str, p: dict) -> dict[ChannelType, str]:
        result = {}
        sections = text.split("---")
        for section in sections:
            section = section.strip()
            if section.startswith("**TWITTER**") or section.upper().startswith("TWITTER"):
                result[ChannelType.TWITTER] = section
            elif section.startswith("**TELEGRAM**") or section.upper().startswith("TELEGRAM"):
                result[ChannelType.TELEGRAM] = section
            elif section.startswith("**FACEBOOK**") or section.upper().startswith("FACEBOOK"):
                result[ChannelType.FACEBOOK] = section
            elif section.startswith("**INSTAGRAM**") or section.upper().startswith("INSTAGRAM"):
                result[ChannelType.INSTAGRAM] = section
            elif section.startswith("**PINTEREST**") or section.upper().startswith("PINTEREST"):
                result[ChannelType.PINTEREST] = section
            elif section.startswith("**WORDPRESS**") or section.upper().startswith("WORDPRESS"):
                result[ChannelType.WORDPRESS] = section
            elif section.startswith("**REDDIT**") or section.upper().startswith("REDDIT"):
                result[ChannelType.REDDIT] = section
            elif section.startswith("**NEWSLETTER**") or section.upper().startswith("NEWSLETTER"):
                result[ChannelType.NEWSLETTER] = section

        for channel in ChannelType:
            if channel not in result:
                result[channel] = self._channel_fallback(channel, p)
        return result

    def _channel_fallback(self, channel: ChannelType, p: dict) -> str:
        link = p["affiliate_link"]
        name = p["product_name"]
        disc = p["discount"]
        price = p["current_price"]

        fallbacks = {
            ChannelType.TWITTER: f"1/4 {name} in sconto!\n2/4 {disc}% di sconto\n3/4 {link}\n4/4 Affrettati!",
            ChannelType.TELEGRAM: f"🏷️ {name}\n💰 {disc}% di sconto!\n🔗 {link}",
            ChannelType.FACEBOOK: f"{name} è in offerta con il {disc}% di sconto! Prezzo: {price}€. Acquistalo qui 👉 {link}",
            ChannelType.INSTAGRAM: f"Slide 1: {name}\nSlide 2: {disc}% OFF\nSlide 3: Qualità\nSlide 4: Prezzo {price}€\nSlide 5: Link in bio!",
            ChannelType.PINTEREST: f"{name} - {disc}% di sconto! Prezzo {price}€. {link} #offerte #shopping",
            ChannelType.WORDPRESS: f"Titolo: {name} in offerta\nMeta: {name} scontato del {disc}%\n\n<h2>L'offerta</h2>\n{name} è disponibile a soli {price}€.\n\n<h2>Caratteristiche</h2>\nProdotto di qualità.\n\n<h2>Perché acquistarlo</h2>\nCon il {disc}% di sconto, è il momento giusto.\n\n{link}",
            ChannelType.REDDIT: f"Ho trovato {name} a {price}€ ({disc}% di sconto). Pensavo potesse interessare a qualcuno! {link}",
            ChannelType.NEWSLETTER: f"Oggetto: {name} in offerta!\n\nCiao,\nho trovato questa offerta: {name} a {price}€ ({disc}% di sconto).\n\n{link}",
        }
        return fallbacks.get(channel, "")

    def _fallback_templates(self, p: dict) -> dict[ChannelType, str]:
        return {channel: self._channel_fallback(channel, p) for channel in ChannelType}
