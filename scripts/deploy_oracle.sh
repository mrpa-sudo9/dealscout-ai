#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# DealScout AI - Oracle Cloud Free Tier Deploy Script
# =============================================================================
# Esegui UNA SOLA VOLTA sul VM:
#   curl -fsSL https://raw.githubusercontent.com/.../deploy.sh | bash
# =============================================================================

REPO="${1:-}"  # Opzionale: URL git (es. https://github.com/user/dealscout.git)
BRANCH="main"
INSTALL_DIR="/opt/dealscout"
APP_USER="dealscout"
APP_GROUP="dealscout"

echo "=== DealScout AI - Oracle Cloud Deployment ==="
echo ""

# --- Verifica root ---
if [ "$EUID" -ne 0 ]; then
    echo "ERRORE: Esegui come root (sudo)."
    exit 1
fi

# --- 1. System update + dipendenze ---
echo "[1/7] Installazione dipendenze di sistema..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    git curl wget \
    sqlite3 \
    nginx \
    certbot python3-certbot-nginx \
    fail2ban \
    ufw \
    > /dev/null 2>&1
echo "  ✓ Fatto"

# --- 2. Crea utente dedicato ---
echo "[2/7] Creazione utente dealscout..."
if ! id -u $APP_USER > /dev/null 2>&1; then
    useradd -m -s /bin/bash -d $INSTALL_DIR $APP_USER
    echo "  ✓ Utente $APP_USER creato"
else
    echo "  ✓ Utente $APP_USER già esistente"
fi

# --- 3. Clona/copia progetto ---
echo "[3/7] Setup progetto..."
if [ -d "$INSTALL_DIR" ] && [ -n "$(ls -A $INSTALL_DIR 2>/dev/null)" ]; then
    echo "  ✓ Progetto già presente in $INSTALL_DIR"
elif [ -n "$REPO" ]; then
    sudo -u $APP_USER git clone --depth 1 --branch $BRANCH "$REPO" "$INSTALL_DIR"
    echo "  ✓ Clonato da $REPO"
else
    # Se non c'è repo, crea struttura e userà rsync/scp
    mkdir -p $INSTALL_DIR
    chown $APP_USER:$APP_GROUP $INSTALL_DIR
    echo "  ⚠️  Directory creata: $INSTALL_DIR"
    echo "  ⚠️  Copia i file localmente con:"
    echo "     rsync -avz --exclude .venv --exclude .git ./ ubuntu@<IP>:$INSTALL_DIR"
fi

# --- 4. Ambiente Python ---
echo "[4/7] Configurazione ambiente Python..."
cd $INSTALL_DIR
sudo -u $APP_USER python3 -m venv venv
sudo -u $APP_USER ./venv/bin/pip install --quiet --upgrade pip
sudo -u $APP_USER ./venv/bin/pip install --quiet -e .
sudo -u $APP_USER ./venv/bin/playwright install chromium 2>/dev/null || true
echo "  ✓ Venv + dipendenze installate"

# --- 5. Configurazione .env ---
echo "[5/7] Configurazione ambiente..."
ENV_FILE="$INSTALL_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'EOF'
# === DealScout AI - Config ===
DATABASE_URL=sqlite+aiosqlite:///data/dealscout.db
LOG_LEVEL=INFO
DATA_DIR=./data
MIN_DISCOUNT_PERCENT=20
SCRAPE_FREQUENCY_HOURS=6
MAX_CONCURRENT_SCRAPES=3
REQUEST_TIMEOUT=30

# 🔑 LLM (almeno uno richiesto - Gemini è gratis!)
# Ottieni Gemini key: https://aistudio.google.com/apikey
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

# 🔑 API Keys opzionali
GROQ_API_KEY=
AMAZON_ASSOCIATES_TAG=dealscout-21
TWITTER_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHANNEL_ID=
EOF
    chown $APP_USER:$APP_GROUP "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "  ✓ .env creato in $ENV_FILE"
    echo "  ⚠️  MODIFICA LE API KEY in $ENV_FILE prima di avviare!"
else
    echo "  ✓ .env già esistente"
fi

# --- 6. Inizializza DB + setup ---
echo "[6/7] Inizializzazione database..."
mkdir -p "$INSTALL_DIR/data" "$INSTALL_DIR/data/logs"
chown -R $APP_USER:$APP_GROUP "$INSTALL_DIR/data"
sudo -u $APP_USER ./venv/bin/dealscout init 2>/dev/null || \
    sudo -u $APP_USER ./venv/bin/python3 -c "
import asyncio; from database.session import init_db; asyncio.run(init_db())
" 2>/dev/null
echo "  ✓ Database inizializzato"

# --- 7. Systemd service ---
echo "[7/7] Installazione systemd service..."
cat > /etc/systemd/system/dealscout.service << 'SERVICE'
[Unit]
Description=DealScout AI - Autonomous Income Engine
After=network.target

[Service]
Type=oneshot
User=dealscout
Group=dealscout
WorkingDirectory=/opt/dealscout
ExecStart=/opt/dealscout/venv/bin/dealscout scan
MemoryMax=500M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
SERVICE

cat > /etc/systemd/system/dealscout.timer << 'TIMER'
[Unit]
Description=DealScout AI - Scan ogni 6 ore
Requires=dealscout.service

[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00
RandomizedDelaySec=300
Persistent=true

[Install]
WantedBy=timers.target
TIMER

systemctl daemon-reload
systemctl enable dealscout.timer --quiet
systemctl start dealscout.timer
echo "  ✓ Timer systemd attivato (scan ogni 6h)"

# --- Firewall ---
echo ""
echo "=== Configurazione firewall ==="
ufw --force reset > /dev/null 2>&1
ufw default deny incoming > /dev/null
ufw default allow outgoing > /dev/null
ufw allow ssh > /dev/null
ufw allow http > /dev/null
ufw allow https > /dev/null
ufw --force enable > /dev/null 2>&1 || true
echo "  ✓ Firewall attivo (SSH, HTTP, HTTPS)"

# --- Fail2ban ---
systemctl enable fail2ban --quiet 2>/dev/null || true
systemctl start fail2ban 2>/dev/null || true
echo "  ✓ Fail2ban attivo"

# --- Riepilogo ---
echo ""
echo "=========================================="
echo "  ✅ DealScout AI installato!"
echo "=========================================="
echo ""
echo "  📁 Installazione: $INSTALL_DIR"
echo "  👤 Utente:        $APP_USER"
echo "  🕐 Scan ogni:     6 ore (timer systemd)"
echo ""
echo "  ⚠️  PASSI SUCCESSIVI:"
echo "  1. Modifica le API key:"
echo "     nano $INSTALL_DIR/.env"
echo ""
echo "  2. Avvia subito una scansione:"
echo "     systemctl start dealscout.service"
echo ""
echo "  3. Controlla i log:"
echo "     journalctl -u dealscout.service -f"
echo ""
echo "  4. Per aggiornare il progetto:"
echo "     cd $INSTALL_DIR && git pull && ./venv/bin/pip install -e ."
echo ""
echo "=========================================="
