#!/bin/bash
# Stop all running bot instances

echo "🛑 Stopping all bot instances..."

# Find and kill all bot_main.py processes
pkill -9 -f "bot_main.py" 2>/dev/null

sleep 1

# Check if any are still running
REMAINING=$(ps aux | grep "bot_main.py" | grep -v grep)

if [ -z "$REMAINING" ]; then
    echo "✅ All bot instances stopped successfully!"
else
    echo "⚠️  Some processes may still be running:"
    echo "$REMAINING"
    echo ""
    echo "You may need to kill them manually:"
    echo "$REMAINING" | awk '{print "kill -9 " $2}'
fi

