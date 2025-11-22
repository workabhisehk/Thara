#!/bin/bash
# Script to run bot with full debugging and show real-time errors

cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Kill any existing bot instances
echo "🛑 Stopping any running bot instances..."
pkill -9 -f "bot_main.py" 2>/dev/null
pkill -9 -f "run_bot_with_debug.py" 2>/dev/null
sleep 2

echo "🚀 Starting bot with full debugging..."
echo "=" 
echo "Press Ctrl+C to stop"
echo "="
echo ""

# Run bot with debug script
python scripts/run_bot_with_debug.py 2>&1 | tee bot_output.log

