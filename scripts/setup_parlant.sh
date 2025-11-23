#!/bin/bash
# Setup script for Parlant integration

set -e

echo "=========================================="
echo "Parlant Integration Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Please create a .env file with your configuration."
    exit 1
fi

echo "✅ .env file found"

# Check if Parlant is installed
if python -c "import parlant.sdk" 2>/dev/null; then
    echo "✅ Parlant SDK is installed"
else
    echo "❌ Parlant SDK not installed"
    echo "   Installing Parlant..."
    pip install parlant
    echo "✅ Parlant installed"
fi

# Check for required environment variables
echo ""
echo "Checking environment variables..."

if grep -q "USE_PARLANT" .env; then
    USE_PARLANT=$(grep "USE_PARLANT" .env | cut -d '=' -f2 | tr -d ' ')
    if [ "$USE_PARLANT" = "true" ] || [ "$USE_PARLANT" = "True" ] || [ "$USE_PARLANT" = "1" ]; then
        echo "✅ USE_PARLANT is set to true"
    else
        echo "⚠️  USE_PARLANT is set to: $USE_PARLANT"
        echo "   Setting USE_PARLANT=true..."
        if grep -q "^USE_PARLANT" .env; then
            sed -i.bak 's/^USE_PARLANT=.*/USE_PARLANT=true/' .env
        else
            echo "USE_PARLANT=true" >> .env
        fi
        echo "✅ USE_PARLANT set to true"
    fi
else
    echo "⚠️  USE_PARLANT not found in .env"
    echo "   Adding USE_PARLANT=true..."
    echo "USE_PARLANT=true" >> .env
    echo "✅ USE_PARLANT added to .env"
fi

# Check for OPENAI_API_KEY
if grep -q "OPENAI_API_KEY" .env && ! grep -q "^OPENAI_API_KEY=$" .env; then
    echo "✅ OPENAI_API_KEY is set"
else
    echo "⚠️  OPENAI_API_KEY not set or empty"
    echo "   Please set OPENAI_API_KEY in your .env file"
fi

# Check for TELEGRAM_BOT_TOKEN
if grep -q "TELEGRAM_BOT_TOKEN" .env && ! grep -q "^TELEGRAM_BOT_TOKEN=$" .env; then
    echo "✅ TELEGRAM_BOT_TOKEN is set"
else
    echo "⚠️  TELEGRAM_BOT_TOKEN not set or empty"
    echo "   Please set TELEGRAM_BOT_TOKEN in your .env file"
fi

# Check for DATABASE_URL
if grep -q "DATABASE_URL" .env && ! grep -q "^DATABASE_URL=$" .env; then
    echo "✅ DATABASE_URL is set"
else
    echo "⚠️  DATABASE_URL not set or empty"
    echo "   Please set DATABASE_URL in your .env file"
fi

echo ""
echo "=========================================="
echo "Running Parlant Integration Tests"
echo "=========================================="
echo ""

# Run test script
python scripts/test_parlant_integration.py

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review the test results above"
echo "2. Start the bot: python bot_main.py"
echo "3. Send a test message on Telegram"
echo ""

