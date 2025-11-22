# Quick Start Guide - Deploy & Test Locally

## Step 1: Setup Environment (5 minutes)

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install/update dependencies
pip install -r requirements.txt

# 3. Create .env file (if not exists)
cp .env.example .env  # or create manually
```

## Step 2: Configure .env File

Edit `.env` file with your credentials:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
OPENAI_API_KEY=your_openai_key
DATABASE_URL=postgresql://user:password@host:port/dbname
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Optional
GEMINI_API_KEY=your_gemini_key  # Fallback LLM
SENTRY_DSN=your_sentry_dsn      # Error tracking
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Step 3: Validate Configuration

```bash
# Validate environment variables
python scripts/validate_environment.py

# Test database connection
python scripts/test_db_connection.py
```

## Step 4: Setup Database

```bash
# Run migrations to create tables
alembic upgrade head

# Verify tables created
python -c "from database.connection import AsyncSessionLocal; print('✅ DB OK')"
```

## Step 5: Run Tests

```bash
# Run adaptive learning tests
python test_adaptive_learning.py

# Should output: ✅ All tests passed! (5/5)
```

## Step 6: Start the Bot

```bash
# Start bot (will use polling)
python bot_main.py
```

**Expected Output:**
```
============================================================
Starting AI Productivity Agent Bot
============================================================
✅ Environment validation passed
Creating Telegram application...
Setting up handlers...
✅ Bot ready to start polling
============================================================
👋 Hi! Starting bot...
```

## Step 7: Test the Bot

1. **Open Telegram** and find your bot
2. **Send `/start`** - Should initiate onboarding
3. **Complete onboarding**:
   - Select pillars
   - Set work hours
   - Set timezone
   - Add initial tasks
4. **Test commands**:
   - `/tasks` - View tasks
   - `/insights` - View adaptive learning insights
   - `/calendar` - Calendar operations
   - `/help` - Show help

## Step 8: Test Adaptive Learning

1. **Create tasks**:
   - Send: "Add task: Review code"
   - Send: "Add task: Review PR #123"
   - Create 3+ similar tasks

2. **Wait for patterns** (or trigger manually):
   - Patterns detected after 3+ occurrences
   - Check `/insights` command

3. **Enable flow**:
   - In insights, click "Enable" on flow suggestion
   - Verify flow is enabled

4. **Test corrections**:
   - Create task with AI suggestion
   - Change pillar/priority
   - Repeat 3+ times
   - Check if AI learns from corrections

## Troubleshooting

### Bot Won't Start
```bash
# Check environment
python scripts/validate_environment.py

# Check logs
tail -f bot.log
```

### Database Issues
```bash
# Test connection
python scripts/test_db_connection.py

# Check URL format
python scripts/validate_db_url.py
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Quick Commands Reference

```bash
# Validate setup
python scripts/validate_environment.py

# Run tests
python test_adaptive_learning.py

# Start bot
python bot_main.py

# Check logs
tail -f bot.log

# Check running processes
ps aux | grep bot_main.py
```

## Success Indicators

✅ Bot starts without errors  
✅ Environment validation passes  
✅ Bot responds to `/start`  
✅ Tasks can be created  
✅ `/insights` shows learning data  
✅ Scheduled jobs run (check-ins every 30 min)  

## Next Steps

Once deployed and tested locally:
- Test all features end-to-end
- Monitor logs for any issues
- Check adaptive learning is tracking patterns
- Verify scheduled jobs are running

For detailed deployment options (Railway, Render, etc.), see:
- `docs/DEPLOYMENT.md`
- `DEPLOYMENT_CHECKLIST.md`

Happy testing! 🚀
