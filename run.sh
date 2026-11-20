#!/usr/bin/env bash
# Kerala IT Parks Job Tracker - 100% Free, Private & Local Launcher
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "  Kerala IT Parks Job Tracker (Free, Local & Private)     "
echo "  Technopark • Infopark • Cyberpark • UL Cyberpark        "
echo "=========================================================="

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 is required but not found. Please install Python 3."
    exit 1
fi

echo "[*] Checking local dependencies..."
python3 -c "import flask, bs4" 2>/dev/null || {
    echo "[*] Installing required local packages (Flask, BeautifulSoup4)..."
    python3 -m pip install --break-system-packages --user flask beautifulsoup4 requests
}

echo "[*] Starting local web server on http://127.0.0.1:5000 ..."
echo "[*] Press Ctrl+C at any time to stop the server."
echo ""

exec python3 app.py

