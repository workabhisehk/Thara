#!/bin/bash
# Verification script for Parlant setup

echo "=========================================="
echo "Parlant Setup Verification"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# Check 1: Parlant SDK
echo "1. Checking Parlant SDK installation..."
if python -c "import parlant.sdk" 2>/dev/null; then
    echo "   ✅ Parlant SDK installed"
    VERSION=$(python -c "import parlant.sdk as p; print(getattr(p, '__version__', 'unknown'))" 2>/dev/null || echo "unknown")
    echo "   Version: $VERSION"
else
    echo "   ❌ Parlant SDK not installed"
    echo "   Run: pip install parlant"
    ((ERRORS++))
fi
echo ""

# Check 2: Environment Variables
echo "2. Checking environment variables..."
if [ -f .env ]; then
    echo "   ✅ .env file exists"
    
    if grep -q "USE_PARLANT=true" .env; then
        echo "   ✅ USE_PARLANT=true"
    else
        echo "   ⚠️  USE_PARLANT not set to true"
        ((WARNINGS++))
    fi
    
    if grep -q "OPENAI_API_KEY" .env && ! grep -q "^OPENAI_API_KEY=$" .env; then
        echo "   ✅ OPENAI_API_KEY is set"
    else
        echo "   ❌ OPENAI_API_KEY not set"
        ((ERRORS++))
    fi
    
    if grep -q "TELEGRAM_BOT_TOKEN" .env && ! grep -q "^TELEGRAM_BOT_TOKEN=$" .env; then
        echo "   ✅ TELEGRAM_BOT_TOKEN is set"
    else
        echo "   ❌ TELEGRAM_BOT_TOKEN not set"
        ((ERRORS++))
    fi
else
    echo "   ❌ .env file not found"
    ((ERRORS++))
fi
echo ""

# Check 3: Integration Files
echo "3. Checking integration files..."
FILES=(
    "agents_parlant/__init__.py"
    "agents_parlant/agent.py"
    "agents_parlant/tools.py"
    "agents_parlant/telegram_adapter.py"
    "telegram_bot/handlers/start.py"
    "config.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file missing"
        ((ERRORS++))
    fi
done
echo ""

# Check 4: Tools
echo "4. Checking tools..."
if python -c "from agents_parlant.tools import get_user_tasks, create_user_task, get_calendar_events, create_calendar_event, get_user_info" 2>/dev/null; then
    echo "   ✅ All 5 tools importable"
else
    echo "   ⚠️  Some tools may not be importable"
    ((WARNINGS++))
fi
echo ""

# Check 5: Configuration
echo "5. Checking configuration..."
if python -c "from config import settings; print('USE_PARLANT:', settings.use_parlant)" 2>/dev/null | grep -q "True"; then
    echo "   ✅ Configuration loads correctly"
    echo "   USE_PARLANT: $(python -c 'from config import settings; print(settings.use_parlant)' 2>/dev/null)"
else
    echo "   ⚠️  Configuration may not be loading correctly"
    ((WARNINGS++))
fi
echo ""

# Summary
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo "✅ All checks passed! Parlant is ready to use."
        echo ""
        echo "Next steps:"
        echo "1. Start the bot: python bot_main.py"
        echo "2. Send a test message on Telegram"
        echo "3. Monitor logs for Parlant activity"
    else
        echo "⚠️  Setup complete with warnings."
        echo "   Review warnings above and fix if needed."
        echo ""
        echo "You can still start the bot: python bot_main.py"
    fi
else
    echo "❌ Setup incomplete. Please fix errors above."
    exit 1
fi

echo ""

