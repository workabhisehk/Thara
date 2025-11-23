#!/bin/bash
# Restart the bot

cd "$(dirname "$0")/.."

echo "Stopping any running bot instances..."
pkill -f "bot_main.py" || echo "No running bot found"

sleep 2

echo "Starting bot..."
source venv/bin/activate
python bot_main.py

