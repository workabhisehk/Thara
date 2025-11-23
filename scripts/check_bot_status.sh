#!/bin/bash
# Check bot status and diagnose issues

echo "=========================================="
echo "  Thara Bot Status Check"
echo "=========================================="
echo ""

# Check if bot is running
echo "1. Checking if bot is running..."
if pgrep -f "bot_main.py" > /dev/null; then
    echo "✅ Bot is running"
    ps aux | grep -i "bot_main\|python.*bot" | grep -v grep
else
    echo "❌ Bot is NOT running"
fi
echo ""

# Check .env file
echo "2. Checking .env file..."
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    
    # Check critical variables
    if grep -q "TELEGRAM_BOT_TOKEN=" .env && ! grep -q "TELEGRAM_BOT_TOKEN=your_" .env; then
        echo "✅ TELEGRAM_BOT_TOKEN is set"
    else
        echo "⚠️  TELEGRAM_BOT_TOKEN not configured"
    fi
    
    if grep -q "DATABASE_URL=" .env && ! grep -q "DATABASE_URL=postgresql://user:password" .env; then
        echo "✅ DATABASE_URL is set"
    else
        echo "⚠️  DATABASE_URL not configured"
    fi
    
    if grep -q "OPENAI_API_KEY=" .env && ! grep -q "OPENAI_API_KEY=your_" .env; then
        echo "✅ OPENAI_API_KEY is set"
    else
        echo "⚠️  OPENAI_API_KEY not configured"
    fi
else
    echo "❌ .env file not found"
fi
echo ""

# Check virtual environment
echo "3. Checking virtual environment..."
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    if [ -f "venv/bin/python" ] || [ -f "venv/Scripts/python.exe" ]; then
        echo "✅ Python executable found"
    fi
else
    echo "❌ Virtual environment not found"
fi
echo ""

# Check recent logs
echo "4. Checking recent logs..."
if [ -f "bot.log" ]; then
    echo "✅ bot.log exists"
    echo ""
    echo "Last 10 lines of bot.log:"
    tail -n 10 bot.log
    echo ""
    echo "Last error (if any):"
    grep -i "error\|exception\|failed" bot.log | tail -n 5 || echo "No recent errors"
else
    echo "⚠️  bot.log not found"
fi
echo ""

# Check database connection
echo "5. Testing database connection..."
if [ -f ".env" ] && [ -d "venv" ]; then
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
    python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from database.connection import check_connection_health
    import asyncio
    result = asyncio.run(check_connection_health())
    if result:
        print('✅ Database connection successful')
    else:
        print('❌ Database connection failed')
except Exception as e:
    print(f'⚠️  Could not check database: {e}')
" 2>/dev/null || echo "⚠️  Could not test database connection"
else
    echo "⚠️  Skipping database check (venv or .env missing)"
fi
echo ""

# Check Telegram bot token
echo "6. Testing Telegram bot token..."
if [ -f ".env" ] && [ -d "venv" ]; then
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
    python3 -c "
import sys
import os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN', '')
if token and token != 'your_telegram_bot_token_here':
    try:
        import requests
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print(f\"✅ Bot token is valid\")
                print(f\"   Bot name: {bot_info.get('first_name', 'N/A')}\")
                print(f\"   Username: @{bot_info.get('username', 'N/A')}\")
            else:
                print(f\"❌ Bot token is invalid: {data.get('description', 'Unknown error')}\")
        else:
            print(f\"❌ Failed to verify token: HTTP {response.status_code}\")
    except Exception as e:
        print(f\"⚠️  Could not verify token: {e}\")
else:
    print('⚠️  TELEGRAM_BOT_TOKEN not set in .env')
" 2>/dev/null || echo "⚠️  Could not test Telegram token"
else
    echo "⚠️  Skipping Telegram check (venv or .env missing)"
fi
echo ""

echo "=========================================="
echo "  Recommendations"
echo "=========================================="
echo ""

if ! pgrep -f "bot_main.py" > /dev/null; then
    echo "To start the bot:"
    echo "  ./scripts/local_deploy.sh"
    echo "  OR"
    echo "  source venv/bin/activate && python bot_main.py"
    echo ""
fi

