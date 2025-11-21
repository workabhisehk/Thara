#!/bin/bash
# Helper script to fix Supabase connection issues

echo "🔍 Supabase Connection Troubleshooting"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Copy .env.example to .env and fill in your values"
    exit 1
fi

echo "✅ .env file found"
echo ""

# Check DATABASE_URL format
echo "Checking DATABASE_URL format..."
DATABASE_URL=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'")

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not found in .env file"
    exit 1
fi

echo "DATABASE_URL format looks correct"
echo ""

# Extract hostname
HOSTNAME=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\).*/\1/p')
echo "Hostname: $HOSTNAME"
echo ""

# Test DNS
echo "Testing DNS resolution..."
if nslookup "$HOSTNAME" > /dev/null 2>&1; then
    echo "✅ DNS resolution successful"
    IP=$(nslookup "$HOSTNAME" | grep "Address:" | tail -1 | awk '{print $2}')
    echo "   Resolves to: $IP"
else
    echo "❌ DNS resolution failed"
    echo ""
    echo "⚠️  This means your Supabase project is PAUSED"
    echo ""
    echo "📋 To fix this:"
    echo "   1. Go to: https://supabase.com/dashboard"
    echo "   2. Sign in to your account"
    echo "   3. Look for your project (it might show as 'Paused')"
    echo "   4. Click on the project"
    echo "   5. Click 'Restore' or 'Resume' button"
    echo "   6. Wait 1-2 minutes for it to wake up"
    echo "   7. After restoring, get a fresh connection string:"
    echo "      - Go to: Settings → Database"
    echo "      - Copy the 'Connection string' (URI format)"
    echo "      - Update DATABASE_URL in .env file"
    echo ""
    echo "   If the project is not paused, the hostname might be wrong."
    echo "   Double-check your connection string from Supabase dashboard."
    exit 1
fi

echo ""
echo "✅ Connection string looks good!"
echo "   You can now test with: python scripts/test_db_connection.py"

