# DealScout AI

Agente AI autonomo per generare rendita passiva tramite arbitraggio di prezzo e marketing affiliato.

## 🌐 Deploy su Oracle Cloud (gratis, forever)

### Prerequisiti
1. Account [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) (4 ARM core, 24 GB RAM — **$0/mese**)
2. Crea una VM **Canonical Ubuntu 22.04/24.04** con:
   - Shape: `VM.Standard.A1.Flex` (4 OCPU, 24 GB RAM)
   - Boot volume: 200 GB
   - SSH key: scarica la chiave privata `.key`

### Deploy (3 minuti)
```bash
# SSH nella VM
ssh -i tua-chiave.key ubuntu@<IP_VM>

# Scarica e lancia lo script
curl -fsSL https://raw.githubusercontent.com/tuo-user/dealscout/main/scripts/deploy_oracle.sh | sudo bash
```

### Configurazione post-deploy
```bash
# 1. Inserisci le API key
sudo nano /opt/dealscout/.env

# 2. Avvia scansione manuale
sudo systemctl start dealscout.service

# 3. Monitora
journalctl -u dealscout.service -f
```

### Aggiornamento
```bash
cd /opt/dealscout && sudo -u dealscout git pull && ./venv/bin/pip install -e .
sudo systemctl start dealscout.service
```

---

## ☁️ Alternativa: GitHub Actions (zero server)

Attiva il workflow `.github/workflows/scan.yml`. Aggiungi i secrets in `Settings → Secrets and variables → Actions`:
- `GROQ_API_KEY`, `TWITTER_API_KEY`, ecc.

Il workflow gira ogni 6 ore gratis (contra 2.000 minuti/mese).

---

## 🚀 Uso locale

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
dealscout init

# Scansione completa
dealscout scan

# Solo una fase
dealscout scan --hunt-only
dealscout scan --affiliate-only

# Performance
dealscout monitor
```

---

## 🏗️ Architettura

| Layer | Componenti |
|-------|-----------|
| **Agenti** | Deal Hunter → Affiliation Manager → Content Creator → Distribution Manager |
| **Scraping** | 12 marketplace (Amazon, eBay, Etsy, AliExpress, Decathlon, Zalando, MediaMarkt, Fnac, Vinted, ManoMano, Walmart, Rakuten) |
| **AI** | Groq (Llama 3.3 70B) / OpenAI fallback per generazione contenuti |
| **Distribuzione** | Twitter, Telegram, Facebook, Instagram, Pinterest, WordPress, Reddit, Newsletter |
| **DB** | SQLite (dev) / PostgreSQL (prod) |
| **Scheduling** | systemd timer (VM) / GitHub Actions (serverless) |

---

## 📊 Stack

Python 3.11+ · SQLAlchemy · httpx · Playwright · Prefect · Groq API · Tweepy · Loguru

## 📄 Licenza

MIT
