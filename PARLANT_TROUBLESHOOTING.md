# Parlant Troubleshooting Guide

## Issue: Bot Shuts Down After Receiving Messages

### Symptoms
- Bot receives messages but doesn't respond
- Bot shuts down right after Parlant initializes
- Logs show "Application received stop signal"

### Root Cause
Parlant server initialization requires `OPENAI_API_KEY` to be in the environment, but it might not be available when the bot process starts.

### Solution

1. **Stop the current bot** (if running):
   ```bash
   pkill -f bot_main.py
   ```

2. **Restart using the start script**:
   ```bash
   bash scripts/start_bot.sh
   ```

   Or manually:
   ```bash
   # Load environment variables
   export $(cat .env | grep -v '^#' | xargs)
   
   # Start bot
   python bot_main.py
   ```

3. **Verify environment**:
   ```bash
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
   ```

### Fix Applied

The code now automatically sets `OPENAI_API_KEY` in the environment when Parlant initializes:

```python
# In agents_parlant/agent.py
if not os.getenv('OPENAI_API_KEY') and settings.openai_api_key:
    os.environ['OPENAI_API_KEY'] = settings.openai_api_key
```

Additionally, error handling has been improved to fallback to LangGraph if Parlant fails.

## Issue: No Response from Bot

### Check 1: Is the bot running?
```bash
ps aux | grep bot_main.py
```

### Check 2: Check logs
```bash
tail -f bot.log
```

### Check 3: Verify Parlant is enabled
```bash
grep USE_PARLANT .env
```

Should show: `USE_PARLANT=true`

## Issue: Parlant Server Fails to Initialize

### Error: "OPENAI_API_KEY is not set"

**Solution**: Ensure the API key is in your `.env` file:
```env
OPENAI_API_KEY=your_key_here
```

Then restart the bot.

### Error: "Tool context parameter error"

This is a known warning from Parlant's internal FastAPI setup. It doesn't affect functionality - tools will work correctly at runtime.

## Issue: Messages Not Being Processed

### Check 1: Verify routing
The message handler should route to Parlant when `USE_PARLANT=true`. Check logs for:
```
Parlant Integration: Processing message from user...
```

### Check 2: Check for errors
Look for error messages in logs:
```bash
grep -i error bot.log | tail -20
```

### Check 3: Test Parlant directly
```bash
python scripts/test_parlant_integration.py
```

## Quick Fixes

### Restart Bot Properly
```bash
# Stop
pkill -f bot_main.py

# Start with environment
bash scripts/start_bot.sh
```

### Disable Parlant Temporarily
If Parlant is causing issues, you can disable it:

1. Edit `.env`:
   ```env
   USE_PARLANT=false
   ```

2. Restart bot

The bot will fallback to LangGraph or natural language handler.

### Check Bot Status
```bash
# Is bot running?
ps aux | grep bot_main.py

# Check recent logs
tail -50 bot.log

# Verify configuration
python -c "from config import settings; print('USE_PARLANT:', settings.use_parlant)"
```

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Bot shuts down | Restart with `bash scripts/start_bot.sh` |
| No response | Check logs, verify bot is running |
| Parlant errors | Check OPENAI_API_KEY, restart bot |
| Messages not processed | Verify USE_PARLANT=true, check routing |
| Tool errors | Check database connection, user onboarding |

## Getting Help

1. **Check logs**: `tail -f bot.log`
2. **Run verification**: `bash scripts/verify_parlant_setup.sh`
3. **Test integration**: `python scripts/test_parlant_integration.py`
4. **Review documentation**: `PARLANT_SETUP.md`

---

**Last Updated**: 2025-11-22

