#!/usr/bin/env bash
# Installer untuk Kali Linux / Debian / Ubuntu
set -euo pipefail
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-pyqt5 firefox-esr
python3 -m venv venv --system-site-packages
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo
echo "Selesai. Jalankan:"
echo "  source venv/bin/activate && python3 main.py"
