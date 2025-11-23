#!/bin/bash
# Start the bot with proper environment setup

cd "$(dirname "$0")/.."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded from .env"
else
    echo "⚠️  .env file not found"
fi

# Ensure OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not set in environment"
    exit 1
fi

echo "Starting bot..."
echo "USE_PARLANT: ${USE_PARLANT:-false}"
echo ""

# Start the bot
python bot_main.py

