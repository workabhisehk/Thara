#!/bin/bash
# Install dependencies in correct order to avoid resolution issues

set -e

echo "=========================================="
echo "Installing Thara Bot Dependencies"
echo "=========================================="

# Step 1: Core dependencies first
echo "📦 Step 1: Installing core dependencies..."
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0
pip install "pydantic>=2.7.4,<3.0.0" pydantic-settings==2.1.0

# Step 2: Database dependencies
echo "📦 Step 2: Installing database dependencies..."
pip install "sqlalchemy>=2.0.25" alembic==1.12.1
pip install psycopg2-binary==2.9.9 asyncpg==0.29.0
pip install pgvector==0.2.4

# Step 3: LangChain core (must come before langgraph)
echo "📦 Step 3: Installing LangChain core..."
pip install "langchain-core>=1.0.0,<2.0.0"
pip install "langchain>=0.3.0,<2.0.0"
pip install "langchain-community>=0.3.0,<1.0.0"
pip install "langchain-openai>=0.2.0,<2.0.0"
pip install "langchain-google-genai>=2.0.0,<4.0.0"

# Step 4: LangGraph (requires langchain-core)
echo "📦 Step 4: Installing LangGraph..."
pip install "langgraph>=0.2.0,<2.0.0"
pip install "langgraph-checkpoint>=3.0.0,<4.0.0"

# Step 5: LlamaIndex (may have conflicts, install last)
echo "📦 Step 5: Installing LlamaIndex..."
pip install llama-index==0.10.57 || echo "⚠️  LlamaIndex install failed, continuing..."
pip install llama-index-vector-stores-postgres==0.1.5 || echo "⚠️  LlamaIndex vector store install failed, continuing..."
pip install llama-index-embeddings-openai==0.1.9 || echo "⚠️  LlamaIndex embeddings install failed, continuing..."

# Step 6: Telegram bot
echo "📦 Step 6: Installing Telegram bot..."
pip install python-telegram-bot==20.7 python-telegram-bot[job-queue]==20.7

# Step 7: Google Calendar
echo "📦 Step 7: Installing Google Calendar API..."
pip install google-api-python-client==2.108.0
pip install google-auth==2.25.2 google-auth-httplib2==0.1.1 google-auth-oauthlib==1.1.0

# Step 8: Scheduling and utilities
echo "📦 Step 8: Installing utilities..."
pip install apscheduler==3.10.4
pip install python-dotenv==1.0.0 httpx==0.25.2 aiohttp==3.9.1
pip install pytz==2023.3 python-dateutil==2.8.2

# Step 9: Error tracking
echo "📦 Step 9: Installing error tracking..."
pip install "sentry-sdk[fastapi]==1.40.0"

# Step 10: Development tools
echo "📦 Step 10: Installing development tools..."
pip install pytest==7.4.3 pytest-asyncio==0.21.1
pip install black==23.11.0 flake8==6.1.0 mypy==1.7.1

echo ""
echo "=========================================="
echo "✅ Dependencies installation complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Configure .env file with your credentials"
echo "2. Run: alembic upgrade head"
echo "3. Test: python scripts/test_langgraph_local.py"
echo "4. Start: python bot_main.py"

