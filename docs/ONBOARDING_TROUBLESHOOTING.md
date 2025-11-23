# Onboarding Troubleshooting Guide

## Issue: Onboarding Agent Not Working

### Symptoms
- User sends `/start` but onboarding doesn't begin
- Onboarding flow stops mid-way
- Messages during onboarding aren't being processed

### Common Causes

#### 1. User Already Marked as Onboarded
If a user is already marked as `is_onboarded=True`, the `/start` command will show a welcome message instead of starting onboarding.

**Solution:**
```bash
# Reset onboarding for a user
python scripts/fix_onboarding.py reset <telegram_id>
```

#### 2. State Mismatch
The conversation state in the database might not match the in-memory state.

**Solution:**
```bash
# Diagnose state issues
python scripts/fix_onboarding.py diagnose <telegram_id>
```

#### 3. Bot Not Running
The bot must be running to process onboarding messages.

**Check:**
```bash
./scripts/check_bot_status.sh
```

**Start bot:**
```bash
./scripts/restart_bot.sh
```

### Diagnostic Steps

1. **Check if bot is running:**
   ```bash
   ps aux | grep bot_main.py
   ```

2. **Check user's onboarding status:**
   ```bash
   python scripts/fix_onboarding.py diagnose <telegram_id>
   ```

3. **Check logs for errors:**
   ```bash
   tail -f bot.log | grep -i onboarding
   ```

4. **Reset onboarding (if needed):**
   ```bash
   python scripts/fix_onboarding.py reset <telegram_id>
   ```

### Onboarding Flow States

The onboarding flow progresses through these states:

1. `ONBOARDING_NAME` - Asking for preferred name
2. `ONBOARDING_PILLARS` - Selecting categories/pillars
3. `ONBOARDING_CUSTOM_PILLAR` - Adding custom pillar (if needed)
4. `ONBOARDING_WORK_HOURS` - Setting work hours
5. `ONBOARDING_TIMEZONE` - Setting timezone
6. `ONBOARDING_INITIAL_TASKS` - Optional: Adding initial tasks
7. `ONBOARDING_HABITS` - Optional: Setting up habits
8. `ONBOARDING_MOOD_TRACKING` - Optional: Enabling mood tracking
9. `IDLE` - Onboarding complete

### Testing Onboarding

1. **Reset a test user:**
   ```bash
   python scripts/fix_onboarding.py reset <your_telegram_id>
   ```

2. **Send `/start` in Telegram**

3. **Follow the prompts:**
   - Provide your name
   - Select categories
   - Set work hours
   - Set timezone
   - Complete optional steps

4. **Check logs:**
   ```bash
   tail -f bot.log
   ```

### Common Issues

#### Issue: "User already onboarded" message
**Cause:** User's `is_onboarded` flag is `True`

**Fix:**
```bash
python scripts/fix_onboarding.py reset <telegram_id>
```

#### Issue: Messages during onboarding not being processed
**Cause:** State might be incorrect or bot not routing correctly

**Fix:**
1. Check state: `python scripts/fix_onboarding.py diagnose <telegram_id>`
2. Reset if needed: `python scripts/fix_onboarding.py reset <telegram_id>`
3. Restart bot: `./scripts/restart_bot.sh`

#### Issue: Onboarding stops at a specific step
**Cause:** Handler error or missing data

**Fix:**
1. Check logs: `tail -f bot.log | grep -i error`
2. Check state: `python scripts/fix_onboarding.py diagnose <telegram_id>`
3. Reset and try again

### Manual Database Fix

If scripts don't work, you can manually fix in the database:

```sql
-- Reset onboarding for a user
UPDATE users 
SET is_onboarded = FALSE, 
    conversation_state = 'onboarding_name',
    conversation_context = '{}'
WHERE telegram_id = <your_telegram_id>;
```

### Getting Help

If issues persist:
1. Check `bot.log` for detailed error messages
2. Run diagnostics: `python scripts/fix_onboarding.py diagnose <telegram_id>`
3. Check bot status: `./scripts/check_bot_status.sh`
4. Review the onboarding handler code: `telegram_bot/handlers/onboarding.py`

