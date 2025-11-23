# Polling vs Scheduled Jobs

## Understanding the Bot's Behavior

### Current Setup: Long Polling

The bot uses **long polling** to receive messages from Telegram. This is the standard and recommended way for Telegram bots to work.

**What you're seeing:**
```
2025-11-22 19:05:14,285 - telegram.ext.ExtBot - DEBUG - No new updates found.
```

This is **normal behavior**. The bot checks Telegram every 10 seconds for new messages. When there are no messages, it logs "No new updates found" (at DEBUG level).

### Why Polling is Necessary

Telegram bots **must** actively check for messages. There are two methods:

1. **Long Polling** (current) - Bot checks Telegram periodically
   - ✅ Works everywhere (no public URL needed)
   - ✅ Simple setup
   - ✅ Works behind firewalls/NAT
   - ⚠️ Checks every 10 seconds (this is normal)

2. **Webhooks** (alternative) - Telegram sends messages to your server
   - ✅ More efficient
   - ✅ Instant delivery
   - ❌ Requires public URL
   - ❌ Requires HTTPS
   - ❌ More complex setup

**For local development, long polling is the only option.**

## Scheduled Jobs (Recurring Triggers)

### ✅ Scheduled Jobs ARE Configured

The scheduler is initialized when the bot starts and runs independently of message polling.

**Scheduled Jobs:**
1. **Daily Kickoff** - 8:00 AM daily
   - Sends daily summary with calendar events and tasks

2. **Check-ins** - Every 30 minutes
   - Sends contextual check-in messages during work hours

3. **Weekly Review** - Sunday 10:00 AM
   - Sends weekly productivity review

4. **Deadline Reminders** - Every hour
   - Checks for upcoming deadlines and sends reminders

5. **Deadline Escalation** - Every 6 hours
   - Escalates overdue tasks

6. **Calendar Sync** - Every 4 hours
   - Syncs Google Calendar events

7. **Time-based Reminders** - Every 30 minutes
   - Sends reminders based on task estimated duration

8. **Recurring Flows** - Every 6 hours
   - Checks for recurring task patterns

### How They Work Together

```
┌─────────────────────────────────────────┐
│         Bot Process                      │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  Telegram Polling (10s interval) │   │
│  │  - Checks for user messages      │   │
│  │  - Only triggers on new messages │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  APScheduler (Background)         │   │
│  │  - Runs scheduled jobs           │   │
│  │  - Independent of polling        │   │
│  │  - Triggers at set times         │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Key Points:**
- Polling only triggers handlers when there's a **new message**
- Scheduled jobs run **independently** in the background
- Both work simultaneously without interfering

## Reducing Log Noise

The "No new updates found" messages are DEBUG logs. To reduce noise:

### Option 1: Reduce Telegram Bot Logging (Recommended)

Already implemented in `bot_main.py`:
```python
logging.getLogger('telegram.ext.ExtBot').setLevel(logging.INFO)
```

This will hide the DEBUG polling messages.

### Option 2: Filter Logs

You can filter logs when viewing:
```bash
tail -f bot.log | grep -v "No new updates found"
```

## Verifying Scheduled Jobs

To check if scheduled jobs are running:

```python
# Check scheduler status
from scheduler.jobs import scheduler
print(f"Scheduler running: {scheduler.running}")
print(f"Jobs: {scheduler.get_jobs()}")
```

Or check logs for scheduler activity:
```bash
grep -i "scheduler\|check-in\|reminder\|daily" bot.log
```

## Switching to Webhooks (Advanced)

If you have a public URL and want to use webhooks instead:

1. **Set up webhook:**
```python
application.run_webhook(
    listen="0.0.0.0",
    port=8000,
    webhook_url="https://your-domain.com/webhook",
    secret_token="your-secret-token"
)
```

2. **Requirements:**
   - Public HTTPS URL
   - Port forwarding (if local)
   - SSL certificate

**For local development, stick with polling.**

## Summary

✅ **Polling is normal** - Bot must check for messages
✅ **Scheduled jobs ARE running** - They work independently
✅ **Both work together** - No conflicts
✅ **Log noise reduced** - DEBUG messages filtered

The bot is working correctly. The 10-second polling is necessary and only triggers handlers when there are actual messages.

