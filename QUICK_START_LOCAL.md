# Quick Start - Local Deployment

Get the Thara bot running locally in 5 minutes!

## Prerequisites

- Python 3.11+
- PostgreSQL database (or Neon DB account)
- Telegram Bot Token
- OpenAI API Key (or Gemini API Key)

## One-Command Setup

### Linux/Mac

```bash
./scripts/local_deploy.sh
```

### Windows

```powershell
python scripts/local_deploy.py
```

### Cross-Platform (Python)

```bash
python scripts/local_deploy.py
```

## What It Does

1. ✅ Checks Python version
2. ✅ Creates virtual environment
3. ✅ Installs all dependencies
4. ✅ Creates `.env` template (if needed)
5. ✅ Validates environment
6. ✅ Runs database migrations
7. ✅ Starts the bot

## Configuration

After running the script, edit `.env` with your credentials:

```env
TELEGRAM_BOT_TOKEN=your_token_here
OPENAI_API_KEY=your_key_here
DATABASE_URL=postgresql://user:pass@host:port/db
```

## Start Bot Manually

If you've already set up:

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Start bot
python bot_main.py
```

## Troubleshooting

**Python version error?**
```bash
python3 --version  # Should be 3.11+
```

**Database connection failed?**
- Check your `DATABASE_URL` in `.env`
- Ensure database is running
- For Neon DB, make sure project isn't paused

**Missing dependencies?**
```bash
pip install -r requirements.txt
```

## Next Steps

1. Send `/start` to your bot on Telegram
2. Complete onboarding
3. Try: "Add task: Review code tomorrow"

## Full Documentation

See `LOCAL_DEPLOYMENT.md` for detailed instructions.

