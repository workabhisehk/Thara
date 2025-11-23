# Local Deployment Guide

This guide will help you deploy and run the Thara bot locally on your machine.

## Prerequisites

Before you begin, make sure you have:

1. **Python 3.11 or higher** installed
   ```bash
   python3 --version  # Should show 3.11+
   ```

2. **PostgreSQL Database** (one of the following):
   - Local PostgreSQL installation
   - Neon DB (free tier available)
   - Supabase (free tier available)
   - Any PostgreSQL-compatible database

3. **API Keys**:
   - Telegram Bot Token (from [@BotFather](https://t.me/botfather))
   - OpenAI API Key (or Gemini API Key as fallback)
   - Google Calendar API credentials (for calendar features)

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run the deployment script
./scripts/local_deploy.sh
```

This script will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Create .env template if needed
- ✅ Validate environment
- ✅ Check database connection
- ✅ Run migrations
- ✅ Start the bot

### Option 2: Manual Setup

#### Step 1: Clone and Navigate

```bash
cd /path/to/Thara
```

#### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env  # If .env.example exists
# Or create .env manually
```

Edit `.env` with your credentials:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# AI/LLM
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Google Calendar
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
TIMEZONE=UTC

# Agent Framework
USE_PARLANT=False  # Set to True to use Parlant instead of LangGraph
```

#### Step 5: Validate Environment

```bash
python scripts/validate_environment.py
```

#### Step 6: Run Database Migrations

```bash
alembic upgrade head
```

#### Step 7: Start the Bot

```bash
python bot_main.py
```

## Running the Bot

### Start the Bot

```bash
# Activate virtual environment first
source venv/bin/activate

# Start the bot
python bot_main.py
```

### Stop the Bot

Press `Ctrl+C` in the terminal where the bot is running.

### Run in Background (Linux/Mac)

```bash
# Using nohup
nohup python bot_main.py > bot.log 2>&1 &

# Or using screen
screen -S thara-bot
python bot_main.py
# Press Ctrl+A then D to detach
# Reattach with: screen -r thara-bot
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | Telegram bot token from BotFather |
| `OPENAI_API_KEY` | ✅ Yes | OpenAI API key (or use GEMINI_API_KEY) |
| `GEMINI_API_KEY` | ⚠️ Optional | Gemini API key (fallback if OpenAI fails) |
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string |
| `GOOGLE_CLIENT_ID` | ⚠️ Optional | For calendar features |
| `GOOGLE_CLIENT_SECRET` | ⚠️ Optional | For calendar features |
| `USE_PARLANT` | ⚠️ Optional | Set to `True` to use Parlant agent |

### Database Setup

#### Using Neon DB (Recommended for Development)

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string
4. Add to `.env` as `DATABASE_URL`

#### Using Local PostgreSQL

1. Install PostgreSQL:
   ```bash
   # macOS
   brew install postgresql
   brew services start postgresql
   
   # Ubuntu/Debian
   sudo apt-get install postgresql
   sudo systemctl start postgresql
   ```

2. Create database:
   ```bash
   createdb thara_bot
   ```

3. Update `.env`:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/thara_bot
   ```

## Troubleshooting

### Common Issues

#### 1. Python Version Error

**Error**: `Python 3.11+ required`

**Solution**: Install Python 3.11 or higher:
```bash
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt-get install python3.11
```

#### 2. Database Connection Failed

**Error**: `Could not connect to database`

**Solutions**:
- Check `DATABASE_URL` in `.env`
- Verify database is running
- Check firewall/network settings
- For Neon DB, ensure project is not paused

#### 3. Missing Dependencies

**Error**: `ModuleNotFoundError`

**Solution**: Reinstall dependencies:
```bash
pip install -r requirements.txt
```

#### 4. Migration Errors

**Error**: `alembic: command not found`

**Solution**: Install alembic:
```bash
pip install alembic
alembic upgrade head
```

#### 5. Greenlet Error

**Error**: `greenlet is required`

**Solution**: Install greenlet:
```bash
pip install greenlet
```

### Debug Mode

Run with debug logging:

```bash
# Set log level to DEBUG in .env
LOG_LEVEL=DEBUG

# Or run with Python debugger
python -m pdb bot_main.py
```

### Check Logs

Logs are written to:
- Console output
- `bot.log` file (in project root)

View logs:
```bash
tail -f bot.log
```

## Development Workflow

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
flake8 .
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## Health Check

Once the bot is running, you can check its health:

```bash
# If FastAPI server is running
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "1.0.0",
  "checks": {
    "api": "ok",
    "database": "ok"
  }
}
```

## Next Steps

After successful deployment:

1. **Test the bot**: Send `/start` to your bot on Telegram
2. **Check logs**: Monitor `bot.log` for any errors
3. **Configure work hours**: Use `/settings` command
4. **Add tasks**: Try natural language like "Add task: Review code tomorrow"

## Production Deployment

For production deployment, see:
- `docs/DEPLOYMENT.md` - Deployment guide
- `deployment/Dockerfile` - Docker configuration
- `deployment/railway.json` - Railway.app configuration

## Support

If you encounter issues:
1. Check the logs: `bot.log`
2. Review `docs/TROUBLESHOOTING.md`
3. Check GitHub issues
4. Review error messages in the console

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/local_deploy.sh` | Full automated deployment |
| `scripts/setup_local.sh` | Quick setup (dependencies only) |
| `scripts/start_bot.sh` | Start bot (assumes setup done) |
| `scripts/stop_bot.sh` | Stop running bot |
| `scripts/validate_environment.py` | Validate .env configuration |

