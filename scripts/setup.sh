#!/usr/bin/env bash
set -euo pipefail

echo "=== DealScout AI Setup ==="

echo "Checking Python version..."
python3 --version 2>&1 | grep -q "3.11\|3.12" || { echo "Python 3.11+ required"; exit 1; }

echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -e .
pip install playwright
playwright install chromium

echo "Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example - EDIT IT with your API keys!"
fi

echo "Creating data directories..."
mkdir -p data/logs

echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Start infrastructure: docker compose up -d"
echo "  3. Initialize DB: python -m src.main"
echo "  4. Run a scan: python -m dags.deal_scan"
echo "  5. Deploy Prefect: prefect deployment build dags/deal_scan.py:deal_scan_flow -n deal-scan"
