#!/bin/bash
set -e

echo "🌫 MIST — Деплой на VPS"

# Клонируем/обновляем
if [ -d "/opt/MIST" ]; then
    cd /opt/MIST
    git pull
else
    git clone <REPO_URL> /opt/MIST
    cd /opt/MIST
fi

# venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env
if [ ! -f .env ]; then
    echo "Создай .env файл в /opt/MIST/.env"
    exit 1
fi

# systemd
sudo cp mist.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mist
sudo systemctl restart mist

echo "✅ MIST запущен!"
echo "sudo systemctl status mist — статус"
echo "sudo journalctl -u mist -f — логи"
