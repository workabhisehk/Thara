#!/bin/bash
# Find and list running bot instances

echo "🔍 Searching for running bot instances..."
echo ""

# Find Python processes running bot_main.py
BOT_PROCESSES=$(ps aux | grep "bot_main.py" | grep -v grep)

if [ -z "$BOT_PROCESSES" ]; then
    echo "✅ No running bot instances found (good!)"
else
    echo "⚠️  Found running bot instance(s):"
    echo ""
    echo "$BOT_PROCESSES"
    echo ""
    echo "To stop them, run:"
    echo "  pkill -f bot_main.py"
    echo ""
    echo "Or kill specific PID:"
    echo "$BOT_PROCESSES" | awk '{print "  kill " $2}'
fi

echo ""
echo "Checking for webhook connections..."
WEBHOOK=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN:-YOUR_TOKEN}/getWebhookInfo" 2>/dev/null)
if echo "$WEBHOOK" | grep -q "url.*http"; then
    echo "⚠️  Webhook is configured:"
    echo "$WEBHOOK" | grep -o '"url":"[^"]*"'
    echo ""
    echo "If using polling, you should delete the webhook:"
    echo "  curl -X POST https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN:-YOUR_TOKEN}/deleteWebhook"
else
    echo "✅ No webhook configured (using polling)"
fi

