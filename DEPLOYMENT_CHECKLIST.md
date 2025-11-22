# Deployment Checklist - AI Productivity Agent Bot

## Pre-Deployment Checklist

### 1. Environment Setup ✅

#### Required Environment Variables
Create a `.env` file in the project root with the following variables:

```bash
# Telegram Bot (Required)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Database (Required)
DATABASE_URL=postgresql://user:password@host:port/database

# AI/LLM (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Google Calendar (Required for calendar features)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=your_redirect_uri

# Optional
GEMINI_API_KEY=your_gemini_api_key  # Optional fallback LLM
SENTRY_DSN=your_sentry_dsn  # Optional error tracking
ENVIRONMENT=production  # or development
LOG_LEVEL=INFO
```

#### Validate Environment
```bash
python scripts/validate_environment.py
```

### 2. Dependencies Installation ✅

```bash
# Activate virtual environment (if using)
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "telegram|langchain|sqlalchemy|psycopg"
```

### 3. Database Setup ✅

#### Create Database Tables
```bash
# Using Alembic migrations
alembic upgrade head

# OR manually create tables (if not using migrations)
python scripts/init_db.py
```

#### Verify Database Connection
```bash
python scripts/test_db_connection.py
```

### 4. Pre-Deployment Tests ✅

#### Run Automated Tests
```bash
# Test adaptive learning features
python test_adaptive_learning.py

# Should output: ✅ All tests passed! (5/5)
```

#### Syntax Check
```bash
python -m py_compile bot_main.py
python -m py_compile telegram_bot/bot.py
python -m py_compile memory/adaptive_learning.py
python -m py_compile memory/flow_enabler.py
```

### 5. Configuration Verification ✅

#### Check Configuration Loading
```bash
python -c "from config import settings; print('✅ Config loaded:', settings.telegram_bot_token[:10] + '...')"
```

#### Check Database Connection String
```bash
python scripts/validate_db_url.py
```

## Deployment Steps

### Step 1: Prepare Deployment Environment

```bash
# 1. Ensure .env file exists and is configured
cat .env | grep -E "TELEGRAM_BOT_TOKEN|DATABASE_URL|OPENAI_API_KEY"

# 2. Check database is accessible
python scripts/test_db_connection.py

# 3. Verify all dependencies are installed
pip check
```

### Step 2: Database Migration

```bash
# Run migrations to ensure database schema is up to date
alembic upgrade head

# Verify tables exist
python -c "
from database.connection import AsyncSessionLocal
from database.models import User, Task, Habit, LearningFeedback
import asyncio

async def check():
    async with AsyncSessionLocal() as session:
        print('✅ Database connection successful')

asyncio.run(check())
"
```

### Step 3: Start the Bot

```bash
# Start the bot
python bot_main.py
```

#### Expected Output:
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

### Step 4: Verify Bot is Running

1. **Check Logs**: Look for "Bot initialized and ready"
2. **Send Test Message**: Send `/start` to your bot on Telegram
3. **Verify Response**: Bot should respond with onboarding flow

### Step 5: Test Key Features

#### Test Checklist:

- [ ] **Onboarding**
  - Send `/start` to bot
  - Complete onboarding flow (pillars, work hours, timezone)
  - Verify user is saved in database

- [ ] **Task Creation**
  - Send "Add task: Test task" via natural language
  - Or use `/tasks` command
  - Verify task is created

- [ ] **Insights Command**
  - Send `/insights` command
  - Verify insights are displayed (may be empty if no patterns yet)

- [ ] **Calendar Integration**
  - Send `/calendar` command
  - Verify calendar connection (or setup instructions)

- [ ] **Adaptive Learning**
  - Create multiple tasks in same category
  - Create tasks at similar times
  - Wait for patterns to be detected
  - Check `/insights` again

- [ ] **Scheduled Jobs**
  - Wait for scheduled check-in (every 30 minutes)
  - Wait for daily kickoff (at work start hour)
  - Verify scheduled jobs are running

## Post-Deployment Testing

### Test Adaptive Learning Flow

1. **Create Recurring Pattern**:
   ```
   - Add task: "Review code" (Monday)
   - Wait a week
   - Add task: "Review code" (Next Monday)
   - Wait another week
   - Add task: "Review code" (Next Monday)
   ```

2. **Check Pattern Detection**:
   - Send `/insights` command
   - Should show recurring pattern detected

3. **Enable Flow**:
   - In insights, click "Enable" on recurring flow suggestion
   - Verify flow is enabled

4. **Test Reminder**:
   - Wait for reminder time (or check scheduled job)
   - Verify reminder is sent
   - Test creating task from reminder

### Test Correction Learning

1. **Create Task with AI Suggestion**:
   - Send "Add task: Work on project"
   - AI suggests pillar "work"
   - Change pillar to "personal"

2. **Repeat Corrections**:
   - Repeat similar corrections 3+ times
   - Check if learning occurs

3. **Verify Learning**:
   - Create similar task again
   - AI should adapt suggestion based on corrections

## Troubleshooting

### Common Issues

#### 1. Bot Won't Start
```bash
# Check environment variables
python scripts/validate_environment.py

# Check logs
tail -f bot.log

# Check for port conflicts
lsof -i :8000  # or your configured port
```

#### 2. Database Connection Issues
```bash
# Test connection
python scripts/test_db_connection.py

# Check DATABASE_URL format
python scripts/validate_db_url.py

# Verify database is running
psql $DATABASE_URL -c "SELECT 1;"
```

#### 3. Missing Dependencies
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall

# Check for conflicts
pip check
```

#### 4. Scheduled Jobs Not Running
```bash
# Check scheduler initialization in logs
grep "Scheduler" bot.log

# Verify APScheduler is installed
pip show apscheduler

# Check if scheduler is starting
python -c "from scheduler.jobs import init_scheduler; import asyncio; asyncio.run(init_scheduler())"
```

#### 5. Telegram Bot Not Responding
```bash
# Verify bot token
python -c "from config import settings; print(settings.telegram_bot_token[:10])"

# Test bot token validity
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# Check for rate limiting
tail -f bot.log | grep "rate"
```

### Debug Mode

Run with debug logging:
```bash
LOG_LEVEL=DEBUG python bot_main.py
```

## Monitoring

### Check Bot Status
```bash
# Check if bot process is running
ps aux | grep bot_main.py

# Check logs
tail -f bot.log

# Check recent errors
grep "ERROR" bot.log | tail -20
```

### Monitor Scheduled Jobs
```bash
# Check scheduler logs
grep "Scheduler" bot.log | tail -20

# Check job execution
grep -E "check_ins|daily_kickoff|recurring_flows" bot.log | tail -20
```

### Monitor Adaptive Learning
```bash
# Check pattern detection
grep "Pattern detected" bot.log

# Check flow enabling
grep "Enabled flow" bot.log

# Check corrections
grep "correction" bot.log
```

## Quick Start Commands

```bash
# 1. Setup (one-time)
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit .env with your values
python scripts/validate_environment.py
alembic upgrade head

# 2. Run tests
python test_adaptive_learning.py

# 3. Start bot
python bot_main.py

# 4. Test bot
# Open Telegram, find your bot, send /start
```

## Success Criteria

✅ Bot starts without errors  
✅ Environment validation passes  
✅ Database connection successful  
✅ Scheduler initializes  
✅ Bot responds to /start command  
✅ Tasks can be created  
✅ Insights command works  
✅ Scheduled jobs run (check-ins, reminders)  
✅ Adaptive learning tracks patterns  

## Need Help?

1. Check `docs/DEPLOYMENT.md` for detailed deployment instructions
2. Check `docs/TESTING_SUMMARY.md` for test results
3. Review logs: `tail -f bot.log`
4. Run validation: `python scripts/validate_environment.py`

Good luck with deployment! 🚀

